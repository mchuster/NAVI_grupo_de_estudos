import asyncio
import sys
import os
from marshal import load

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

MODEL = "gemini-3.5-flash-lite"

cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "server_demo.py")

PARAMS = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])

async def main() -> None:
    async with stdio_client(PARAMS) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()

            # TODO: liste os resources com sessao.list_resources() e imprima o uri e o nome de cada um
            recursos = await sessao.list_resources()
            for recurso in recursos.resources:
                print(f"- {recurso.uri}: {recurso.name}")

            conteudo = await sessao.read_resource("file:///docs/regras.md")
            regras = conteudo.contents[0].text
            print(regras)

            # TODO: monte um prompt do tipo "Com base nas regras abaixo, responda: posso rodar um DELETE em producao?"
            #       inserindo o texto de "regras" como contexto e envie ao Gemini (reaproveite o client da ponte)
            prompt = f"Com base nas regras abaixo, responda: posso rodar um DELETE em producao?\n\n{regras}"
            resposta = await cliente.aio.models.generate_content(model=MODEL, contents=[prompt])
            print(resposta.text)



if __name__ == "__main__":
    asyncio.run(main())