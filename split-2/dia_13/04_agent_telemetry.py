import importlib
import time

nucleo = importlib.import_module("01_react_loop")
chained = importlib.import_module("02_chained_tools_agent")

VERDE, AMARELO, CINZA, RESET = "\033[92m", "\033[93m", "\033[90m", "\033[0m"


class Telemetria:
    def __init__(self):
        self.turnos = []

    def __call__(self, turno: int, response, segundos: float):
        uso = response.usage_metadata
        # TODO: guarde em self.turnos um dicionario com: turno, segundos, tokens_prompt (uso.prompt_token_count),
        #       tokens_total (uso.total_token_count) e ferramentas (lista de nomes em response.function_calls, ou [])
        # TODO: imprima uma linha colorida por turno: numero, tempo em segundos e ferramentas chamadas
        ferramentas = [chamada.name for chamada in response.function_calls] if response.function_calls else []
        self.turnos.append({
            "turno": turno,
            "segundos": segundos,
            "tokens_prompt": uso.prompt_token_count,
            "tokens_total": uso.total_token_count,
            "ferramentas": ferramentas
        })
        print(f"{AMARELO}Turno {turno}: {segundos:.2f}s, Ferramentas: {', '.join(ferramentas) if ferramentas else 'Nenhuma'}{RESET}")

    def relatorio(self):
        print(f"{VERDE}=== Relatorio do agente ==={RESET}")
        # TODO: imprima o total de turnos, o tempo total, o total de tokens do ultimo turno
        #       (o contexto acumulado) e o turno mais lento
        total_turnos = len(self.turnos)
        tempo_total = sum(turno["segundos"] for turno in self.turnos)
        total_tokens = self.turnos[-1]["tokens_total"] if self.turnos else 0
        turno_mais_lento = max(self.turnos, key=lambda t: t["segundos"]) if self.turnos else None
        print(f"Total de turnos: {total_turnos}")
        print(f"Tempo total: {tempo_total:.2f}s")
        print(f"Total de tokens (ultimo turno): {total_tokens}")
        if turno_mais_lento:
            print(f"Turno mais lento: {turno_mais_lento['turno']} ({turno_mais_lento['segundos']:.2f}s)")


if __name__ == "__main__":
    telemetria = Telemetria()
    inicio = time.perf_counter()
    texto, _ = nucleo.rodar_agente(
        "Quanto a usuaria maria@empresa.com gastou no total?",
        chained.FERRAMENTAS,
        ao_fim_do_turno=telemetria,
    )
    print(texto)
    telemetria.relatorio()
    print(f"{CINZA}Tempo de parede: {time.perf_counter() - inicio:.2f}s{RESET}")