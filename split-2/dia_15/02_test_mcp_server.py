import asyncio
import hashlib
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PARAMS = StdioServerParameters(command=sys.executable, args=["server_utils.py"])
aprovados = 0
falhas = 0


def checar(nome: str, condicao: bool, detalhe: str = "") -> None:
    global aprovados, falhas
    if condicao:
        aprovados += 1
        print(f"  [OK]   {nome}")
    else:
        falhas += 1
        print(f"  [FALHA] {nome} {detalhe}")


async def main() -> None:
    async with stdio_client(PARAMS) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()

            nomes = {t.name for t in (await sessao.list_tools()).tools}
            checar("expoe as 3 ferramentas", nomes == {"calcular_hash_arquivo", "contar_linhas_codigo", "converter_temperatura"})

            r = await sessao.call_tool("converter_temperatura", {"valor": 100, "de": "C", "para": "F"})
            checar("100 C = 212 F", r.content[0].text.startswith("212"), r.content[0].text)

            # TODO: teste calcular_hash_arquivo com um arquivo real (por exemplo, este proprio script):
            #       compare com hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            r = await sessao.call_tool("calcular_hash_arquivo", {"caminho": __file__})
            checar("hash do proprio script", r.content[0].text == hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

            # TODO: teste erro: diretorio inexistente em contar_linhas_codigo; espere r.isError == True
            r = await sessao.call_tool("contar_linhas_codigo", {"diretorio": "/caminho/inexistente", "extensao": ".py"})
            checar("erro com diretorio inexistente", r.isError)

            # TODO: teste erro de tipo: converter_temperatura com "valor": "abc"; espere r.isError == True
            r = await sessao.call_tool("converter_temperatura", {"valor": "abc", "de": "C", "para": "F"})
            checar("erro com valor invalido", r.isError)

            # TODO: teste erro de dominio: unidade "X"; espere isError e a mensagem conter "Unidades validas"
            r = await sessao.call_tool("converter_temperatura", {"valor": 0, "de": "X", "para": "C"})
            checar("erro com unidade invalida", r.isError)

            # Prova de vida: o servidor continua respondendo depois de tantos erros
            r = await sessao.call_tool("converter_temperatura", {"valor": 0, "de": "K", "para": "C"})
            checar("servidor vivo apos os erros", not r.isError, r.content[0].text)

    print(f"\nResumo: {aprovados} aprovados, {falhas} falhas")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    asyncio.run(main())