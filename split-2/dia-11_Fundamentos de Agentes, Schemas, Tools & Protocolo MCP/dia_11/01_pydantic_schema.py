import os
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()
MODEL = "gemini-3.5-flash-lite"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


class PerfilUsuario(BaseModel):
    nome: str = Field(description="Nome Completo do usuário")
    idade: int = Field(ge=0, le=120, description="Idade do usuário")
    habilidades: list[str] = Field(description="Lista de habilidades tecnicas do usuário")
    status_conta: Literal["pendente", "aprovada", "rejeitada"] = Field(description="Status da conta do usuário")


TEXTO = (
    "Oi, sou a Marina Souza, tenho 29 anos e trabalho com Python, SQL e Power BI. "
    "Minha conta ainda esta aguardando aprovacao do time."
)


def extrair_perfil(texto: str) -> PerfilUsuario:
    response = client.models.generate_content(
        model=MODEL,
        contents=f"Extraia o perfil do usuario do texto abaixo.\n\n{texto}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PerfilUsuario,
        ),
    )
    # response.parsed ja vem como instancia de PerfilUsuario
    return response.parsed


if __name__ == "__main__":
    perfil = extrair_perfil(TEXTO)
    print(type(perfil).__name__)
    print(perfil.model_dump_json(indent=2))
    print("\nJSON Schema:")
    print(PerfilUsuario.model_json_schema())