import os
import sys
from pathlib import Path
from typing import Annotated
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from visao import carregar_imagem

load_dotenv()
MODEL = "gemini-3.5-flash-lite"

Coordenada = Annotated[int, Field(ge=0, le=1000, description="Coordenada normalizada de 0 a 1000")]


class ElementoVisual(BaseModel):
    texto_extraido: str = Field(description="Texto exato lido na regiao")
    caixa_delimitadora: list[Coordenada] = Field(
        min_length=4, max_length=4,
        description="Coordenadas [ymin, xmin, ymax, xmax] normalizadas de 0 a 1000"
    )


class AnaliseDocumento(BaseModel):
    elementos: list[ElementoVisual] = Field(description="Lista de textos e suas posicoes")
    codigo_identificador: str | None = Field(default=None,
                                             description="Codigo principal do documento (ex: A101) ou null se ausente")
    relacoes_detectadas: list[str] = Field(description="Relacoes semanticas observadas no diagrama")
    limitacoes_visuais: list[str] = Field(description="Alertas de baixa resolucao, cortes ou incertezas")


def extrair_dados_estruturados(caminho: Path) -> AnaliseDocumento:
    dados, mime, _ = carregar_imagem(caminho)
    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # TODO: Complete a instrucao orientando o modelo a nao inventar campos ausentes.
    prompt = (
        "Analise a imagem técnica fornecida. "
        "Localize todas as caixas de texto com suas coordenadas [ymin, xmin, ymax, xmax], "
        "normalizadas na escala de 0 a 1000. "
        "Se o código identificador não estiver nítido, preencha como null. "
        "Liste em limitacoes_visuais qualquer problema de qualidade ou dúvida. "
        "NÃO invente informações: use apenas o que está visível na imagem. "
        "Se um campo estiver ausente, ilegível ou você não tiver certeza, "
        "preencha com null em vez de adivinhar ou completar com valores prováveis, "
        "e registre o motivo em limitacoes_visuais. "
        "Não crie caixas de texto que não existam na imagem."
    )

    resposta = cliente.models.generate_content(
        model=MODEL,
        contents=[prompt, types.Part.from_bytes(data=dados, mime_type=mime)],
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=AnaliseDocumento
        )
    )

    documento = AnaliseDocumento.model_validate_json(resposta.text or "{}")

    # Validacao de consistencia geometrica
    for item in documento.elementos:
        ymin, xmin, ymax, xmax = item.caixa_delimitadora
        if ymin >= ymax or xmin >= xmax:
            raise ValueError(f"Coordenadas geometricamente invalidas detectadas: {item.caixa_delimitadora}")

    return documento


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python dia_21/ocr.py amostras/diagrama.png")
        sys.exit(1)

    resultado = extrair_dados_estruturados(Path(sys.argv[1]))
    print(resultado.model_dump_json(indent=2))