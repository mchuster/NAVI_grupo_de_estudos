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


# TODO: monte o dicionario FERRAMENTAS mapeando o nome (str) para a funcao Python correspondente
FERRAMENTAS = {
    "calcular_faturamento": calcular_faturamento,
    "consultar_cotacao": consultar_cotacao
}


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



def dividir_metricas(numerador: float, denominador: float) -> dict:
    """Divide duas metricas e retorna a razao (por exemplo, erros por requisicao)."""
    return {"razao": numerador / denominador}


def consultar_servico_externo(servico: str) -> dict:
    """Consulta o status de um servico externo pelo nome."""
    raise ConnectionError(f"Servico '{servico}' temporariamente indisponivel")


def executar_com_seguranca(nome: str, args: dict) -> dict:
    """Executa a ferramenta e transforma qualquer excecao em um resultado estruturado."""
    try:
        # TODO: execute FERRAMENTAS[nome](**args) e retorne {"status": "sucesso", "resultado": ...}
        resultado = FERRAMENTAS[nome](**args)
        return {"status": "sucesso", "resultado": resultado}
    except KeyError:
        return {"status": "falha", "error": f"Ferramenta desconhecida: {nome}"}
    except Exception as erro:
        # TODO: retorne {"status": "falha", "error": <mensagem curta, sem traceback completo>}
        return {"status": "falha", "error": str(erro)}

FERRAMENTAS = {
    "dividir_metricas": dividir_metricas,
    "consultar_servico_externo": consultar_servico_externo,
    "responder": responder,
    "calcular_faturamento": calcular_faturamento,
    "consultar_cotacao": consultar_cotacao,
}

PERGUNTAS = [
    "Qual a razao entre 50 erros e 0 requisicoes?",
    "O servico de pagamentos esta no ar?",
]

# TODO: para cada pergunta, rode o ciclo completo usando executar_com_seguranca no passo de execucao
# e imprima a resposta final do modelo
for pergunta in PERGUNTAS:
    config = types.GenerateContentConfig(
        tools=list(FERRAMENTAS.values()),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part(text=pergunta)])]

    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    if not response.function_calls:
        print(response.text)
        continue

    contents.append(response.candidates[0].content)

    partes_resposta = []
    for chamada in response.function_calls:
        resultado = executar_com_seguranca(chamada.name, chamada.args)
        partes_resposta.append(
            types.Part.from_function_response(name=chamada.name, response=resultado)
        )

    contents.append(types.Content(role="user", parts=partes_resposta))
    response_final = client.models.generate_content(model=MODEL, contents=contents, config=config)
    print(response_final.text)