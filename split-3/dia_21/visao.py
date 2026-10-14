import os
import sys
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()
MODEL = "gemini-3.5-flash-lite"


def carregar_imagem(caminho: Path) -> tuple[bytes, str, Image.Image]:
    """Valida o arquivo em disco e retorna os bytes, o MIME real e a imagem Pillow."""
    if not caminho.is_file() or caminho.stat().st_size > 5_000_000:
        raise ValueError("O arquivo deve existir e ter ate 5 MB.")

    dados = caminho.read_bytes()

    # Validacao de integridade com Pillow (evita renomear .txt para .png)
    with Image.open(BytesIO(dados)) as img:
        img.verify()
        formato = img.format
        largura, altura = img.size

    mime = {"PNG": "image/png", "JPEG": "image/jpeg"}.get(formato or "")
    if not mime:
        raise ValueError(f"Formato nao suportado: {formato}. Use PNG ou JPEG.")

    if largura * altura > 12_000_000:
        raise ValueError("Imagem excede o limite de 12 Megapixels.")

    with Image.open(BytesIO(dados)) as img:
        imagem_pil = img.convert("RGB")

    return dados, mime, imagem_pil


def comparar_modalidades(caminho: Path) -> dict[str, str]:
    """Envia a mesma imagem via bytes e via PIL e compara a clareza da resposta."""
    dados, mime, imagem_pil = carregar_imagem(caminho)

    prompt = (
        "Você é um especialista em auditoria de diagramas de arquitetura de software. "
        "Analise a imagem e responda SOMENTE com base no que está visível, sem inventar "
        "componentes, conexões ou rótulos.\n\n"
        "Responda exatamente nestas seções:\n\n"
        "1. COMPONENTES: liste cada componente (caixas, cilindros, ícones, agrupamentos/camadas), "
        "informando o nome exato escrito na imagem, o tipo técnico provável "
        "(ex.: cliente, API, serviço, banco de dados, cache, serviço externo) e a camada "
        "ou grupo a que pertence, se houver.\n\n"
        "2. SETAS: para CADA seta, escreva no formato 'ORIGEM -> DESTINO', indicando: "
        "a direção exata (a ponta da seta aponta para o DESTINO), o estilo da linha "
        "(contínua ou tracejada), se a seta é unidirecional ou bidirecional e o rótulo "
        "associado (protocolo, ação ou dado), se existir. Não deixe nenhuma seta de fora.\n\n"
        "3. LEGIBILIDADE: se qualquer rótulo, nome de componente ou seta não estiver "
        "100% legível (texto cortado, borrado, sobreposto ou pequeno demais), declare "
        "explicitamente ROTULO_ILEGIVEL no lugar do texto e diga onde ele está "
        "(ex.: 'caixa inferior esquerda'). Se tudo estiver legível, escreva "
        "'Todos os rótulos legíveis'.\n\n"
        "4. FLUXO: resuma em 2 a 3 frases o caminho principal de uma requisição, "
        "da origem até o destino final."
    )

    entradas = {
        "bytes": types.Part.from_bytes(data=dados, mime_type=mime),
        "PIL": imagem_pil
    }

    resultados: dict[str, str] = {}
    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    for modo, entrada in entradas.items():
        resposta = cliente.models.generate_content(
            model=MODEL,
            contents=[prompt, entrada],
            config=types.GenerateContentConfig(temperature=0.0)
        )
        resultados[modo] = resposta.text or "Sem resposta gerada."

    return resultados


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python dia_21/visao.py amostras/diagrama.png")
        sys.exit(1)

    respostas = comparar_modalidades(Path(sys.argv[1]))
    for modo, texto in respostas.items():
        print(f"\n=== Resposta via {modo.upper()} ===")
        print(texto)