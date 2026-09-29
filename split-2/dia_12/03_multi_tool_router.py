import statistics
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
MODEL = "gemini-3.5-flash-lite"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def calcular_faturamento(regiao: str, ano: int) -> dict:
    """Retorna o faturamento anual, em reais, de uma regiao comercial brasileira."""
    base = {"Sul": 1_250_000.0, "Sudeste": 3_400_000.0, "Nordeste": 980_000.0}
    return {"regiao": regiao, "ano": ano, "faturamento": base.get(regiao, 0.0)}


def consultar_cotacao(moeda: str) -> dict:
    """Retorna a cotacao atual em reais de uma moeda estrangeira (USD, EUR ou GBP)."""
    tabela = {"USD": 5.20, "EUR": 5.65, "GBP": 6.60}
    return {"moeda": moeda, "cotacao_brl": tabela[moeda]}


def responder(pergunta: str) -> str:
    config = types.GenerateContentConfig(
        tools=list(FERRAMENTAS.values()),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part(text=pergunta)])]

    # Passo 1 e 2: o modelo decide se quer uma ferramenta
    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    if not response.function_calls:
        return response.text

    # O turno do modelo (com o function_call) precisa entrar no historico
    contents.append(response.candidates[0].content)

    # Passo 3: executar cada chamada pedida
    partes_resposta = []
    for chamada in response.function_calls:
        # TODO: busque a funcao em FERRAMENTAS pelo chamada.name e execute com **chamada.args
        funcao = FERRAMENTAS.get(chamada.name)
        if funcao:
            resultado = funcao(**chamada.args)
        partes_resposta.append(
            types.Part.from_function_response(name=chamada.name, response={"result": resultado})
        )

    # Passo 4: devolver os resultados ao modelo para a resposta final
    contents.append(types.Content(role="user", parts=partes_resposta))
    # TODO: chame generate_content novamente com o historico atualizado e retorne response.text
    response_final = client.models.generate_content(model=MODEL, contents=contents, config=config)
    return response_final.text



def obter_temperatura_servidor(datacenter: str) -> dict:
    """Retorna a temperatura atual em graus Celsius de um datacenter (sp-01, rs-02 ou rj-03)."""
    tabela = {"sp-01": 24.5, "rs-02": 21.0, "rj-03": 27.8}
    return {"datacenter": datacenter, "celsius": tabela[datacenter]}


def verificar_status_banco(cluster: str) -> dict:
    """Retorna o status operacional de um cluster de banco de dados (prod, homolog ou analytics)."""
    # TODO: retorne {"cluster": cluster, "status": ...} com prod="saudavel", homolog="degradado", analytics="offline"
    status = {
        "prod": "saudavel",
        "homolog": "degradado",
        "analytics": "offline"
    }
    return {"cluster": cluster, "status": status.get(cluster, "desconhecido")}


def calcular_desvio_padrao(valores: list[float]) -> float:
    """Calcula o desvio padrao amostral de uma lista com pelo menos 2 numeros."""
    # TODO: use statistics.stdev e arredonde para 2 casas decimais
    if len(valores) < 2:
        raise ValueError("A lista deve conter pelo menos 2 numeros.")
    desvio = statistics.stdev(valores)
    return round(desvio, 2)


def validar_formato_documento(cnpj: str) -> dict:
    """Confere apenas o FORMATO de um CNPJ (14 digitos, com ou sem pontuacao); nao consulta a Receita."""
    # TODO: remova pontuacao, verifique se restam exatamente 14 digitos e retorne {"cnpj": cnpj, "formato_valido": bool}
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
    formato_valido = len(cnpj_limpo) == 14
    return {"cnpj": cnpj, "formato_valido": formato_valido}

FERRAMENTAS = {
    "calcular_faturamento": calcular_faturamento,
    "consultar_cotacao": consultar_cotacao,
    "obter_temperatura_servidor": obter_temperatura_servidor,
    "verificar_status_banco": verificar_status_banco,
    "calcular_desvio_padrao": calcular_desvio_padrao,
    "validar_formato_documento": validar_formato_documento
}


# (prompt, ferramenta_esperada ou None quando NAO deve chamar ferramenta)
BATERIA = [
    ("Qual a temperatura do datacenter rs-02?", "obter_temperatura_servidor"),
    ("O cluster analytics esta funcionando?", "verificar_status_banco"),
    ("Qual o desvio padrao de 10, 12, 9, 15 e 11?", "calcular_desvio_padrao"),
    ("O CNPJ 12.345.678/0001-95 tem formato valido?", "validar_formato_documento"),
    ("Explique em duas frases o que e um cluster de banco de dados.", None),
    ("Para que serve o desvio padrao em monitoramento de servidores?", None),
]

if __name__ == "__main__":
    acertos = 0
    for pergunta, esperada in BATERIA:
        # TODO: descubra qual ferramenta o modelo chamou (ou None) e compare com "esperada".
        # Dica: adapte responder() para tambem retornar o nome da primeira chamada, se houver.
        config = types.GenerateContentConfig(
            tools=list(FERRAMENTAS.values()),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        contents = [types.Content(role="user", parts=[types.Part(text=pergunta)])]
        response = client.models.generate_content(model=MODEL, contents=contents, config=config)
        chamada_modelo = response.function_calls[0].name if response.function_calls else None
        if chamada_modelo == esperada:
            acertos += 1
        pass
    print(f"Roteamento correto: {acertos}/{len(BATERIA)}")