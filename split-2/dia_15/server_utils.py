import hashlib
import sys
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("server-utils")


@mcp.tool()
def calcular_hash_arquivo(
    caminho: Annotated[str, Field(description="Caminho do arquivo local, relativo ou absoluto")],
) -> str:
    """Calcula o hash SHA-256 (em hexadecimal) do conteudo de um arquivo local."""
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise ValueError(f"Arquivo nao encontrado: {caminho}")
    # TODO: leia os bytes do arquivo (arquivo.read_bytes()) e retorne hashlib.sha256(...).hexdigest()
    with open(arquivo, "rb") as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()


@mcp.tool()
def contar_linhas_codigo(
    diretorio: Annotated[str, Field(description="Pasta a ser analisada")],
    extensao: Annotated[str, Field(description="Extensao dos arquivos, com ponto")] = ".py",
) -> dict:
    """Conta arquivos e linhas de codigo de uma pasta (recursivo) para uma extensao."""
    pasta = Path(diretorio)
    if not pasta.is_dir():
        raise ValueError(f"Diretorio nao encontrado: {diretorio}")
    total_arquivos = 0
    total_linhas = 0
    # TODO: percorra pasta.rglob(f"*{extensao}"); para cada arquivo some 1 em total_arquivos
    #       e o numero de linhas do texto (use read_text(errors="ignore").splitlines())
    for arquivo in pasta.rglob(f"*{extensao}"):
        if arquivo.is_file():
            total_arquivos += 1
            with open(arquivo, "r", encoding="utf-8", errors="ignore") as f:
                linhas = f.read().splitlines()
                total_linhas += len(linhas)
    return {"extensao": extensao, "arquivos": total_arquivos, "linhas": total_linhas}


@mcp.tool()
def converter_temperatura(valor: float, de: str, para: str) -> float:
    """Converte temperatura entre C (Celsius), F (Fahrenheit) e K (Kelvin)."""
    unidades = {"C", "F", "K"}
    de, para = de.upper(), para.upper()
    if de not in unidades or para not in unidades:
        raise ValueError("Unidades validas: C, F, K")
    # TODO: converta primeiro para Celsius e depois para a unidade de destino; retorne arredondado a 2 casas
    if de == "C":
        celsius = valor
    elif de == "F":
        celsius = (valor - 32) * 5 / 9
    elif de == "K":
        celsius = valor - 273.15

    if para == "C":
        return round(celsius, 2)
    elif para == "F":
        return round(celsius * 9 / 5 + 32, 2)
    elif para == "K":
        return round(celsius + 273.15, 2)


if __name__ == "__main__":
    print("server-utils iniciado (stdio)", file=sys.stderr)  # logs SEMPRE em stderr
    mcp.run(transport="stdio")