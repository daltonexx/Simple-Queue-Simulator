import yaml
import heapq
import operator # Para sorting no __str__

# Controle do simulador
a = 0
c = 0
M = 0
seed = 0.0
qtd_numeros_aleatorios = 0
numero_previo = 0.0
tempo_global = 0.0
numeros_aleatorios_usados = 0
filas = []

class FilaEProbabilidade:
    def __init__(self, fila, probabilidade, saida=False):
        self.fila = fila
        self.probabilidade = probabilidade
        self.saida = saida

class Fila:
    def __init__(self, Server, Capacity, MinArrival, MaxArrival, MinService, MaxService):
        self.Server = Server
        self.Capacity = Capacity
        self.MinArrival = MinArrival
        self.MaxArrival = MaxArrival
        self.MinService = MinService
        self.MaxService = MaxService
        self.Times = {}
        self.Customers = 0
        self.Loss = 0
        self.Timestamp = 0.0
        self.filas_conectadas = []

    def Chegada(self, e):
        # 1. Atualiza tempos acumulados e tempo global
        tempo_decorrido = e.tempo - self.Timestamp
        self.Times[self.Customers] = self.Times.get(self.Customers, 0.0) + tempo_decorrido
        
        self.Timestamp = e.tempo
        global tempo_global
        tempo_global = e.tempo

        if self.Customers < self.Capacity:
            # 2. Cliente entra e conta como na fila
            self.Customers += 1
            
            # 3. Se há servidores livres (Customers <= Server), agenda o FIM do SERVIÇO (P ou S)
            if self.Customers <= self.Server:
                if len(self.filas_conectadas) > 0:
                    heapq.heappush(eventos, Evento('P', self))
                else:
                    heapq.heappush(eventos, Evento('S', self))
            
            # 4. Se foi chegada externa ('C' na Fila 1), agenda a próxima chegada externa
            if e.tipo == 'C':
                # Reusa 'e' para agendar a próxima chegada externa.
                heapq.heappush(eventos, Evento('C', self))

        else:
            # 5. PERDA DE CLIENTE
            self.Loss += 1
    
    def Passagem(self, e):
        # 1. ATUALIZA ESTADO (Fim do Serviço)
        tempo_decorrido = e.tempo - self.Timestamp
        self.Times[self.Customers] = self.Times.get(self.Customers, 0.0) + tempo_decorrido
        self.Timestamp = e.tempo
        global tempo_global
        tempo_global = e.tempo

        self.Customers -= 1 # Cliente sai do serviço/fila

        # 2. AGENDA PRÓXIMO SERVIÇO, se houver espera (Customers >= Server)
        if self.Customers >= self.Server:
            if len(self.filas_conectadas) != 0:
                heapq.heappush(eventos, Evento('P', self))
            else:
                heapq.heappush(eventos, Evento('S', self))
        
        # 3. Lógica de ENCAMINHAMENTO (Roteamento)
        probabilidade_passagem = nextRandom()
        acumulada = 0
        for rota in self.filas_conectadas:
            acumulada += rota.probabilidade
            if probabilidade_passagem < acumulada:
                if not rota.saida:
                    # Cria um novo evento de "chegada interna" ('A') no tempo atual
                    evento_chegada_proxima_fila = Evento('A', rota.fila, tempo=e.tempo)
                    rota.fila.Chegada(evento_chegada_proxima_fila)
                # Se for 'saida', o cliente simplesmente vai embora.
                return

    def Saida(self, e):
        # 1. ATUALIZA ESTADO (Fim do Serviço)
        tempo_decorrido = e.tempo - self.Timestamp
        self.Times[self.Customers] = self.Times.get(self.Customers, 0.0) + tempo_decorrido
        self.Timestamp = e.tempo
        global tempo_global
        tempo_global = e.tempo

        self.Customers -= 1 # Cliente sai do serviço/fila
        
        # 2. AGENDA PRÓXIMO SERVIÇO, se houver espera (Customers >= Server)
        if self.Customers >= self.Server:
            # Agenda o próximo FIM de SERVIÇO (Saída), já que não há rotas P
            heapq.heappush(eventos, Evento('S', self))

    def __str__(self):
        sb = f"Perda de clientes: {self.Loss}\n"
        
        # OTIMIZAÇÃO: Filtra apenas os estados que tiveram tempo acumulado (> 0) e os ordena.
        estados_alcançados = sorted([estado for estado, tempo in self.Times.items() if tempo > 0.0])
        
        for estado in estados_alcançados:
            tempo = self.Times[estado]
            probabilidade = (tempo / tempo_global) * 100 if tempo_global > 0 else 0
            sb += f"Estado {estado}: tempo = {tempo:.4f} \t probabilidade = {probabilidade:.4f}%\n"
            
        return sb

class Evento:
    def __init__(self, tipo, fila_param=None, tempo=None):
        self.tipo = tipo
        self.fila = fila_param
        
        if tempo is not None:
            self.tempo = tempo
        else:
            # Chegada Externa ('C')
            if tipo == 'C':
                delta_t = ((self.fila.MaxArrival - self.fila.MinArrival) * nextRandom() + self.fila.MinArrival)
                self.tempo = tempo_global + delta_t
            # Serviço ('S' ou 'P')
            else: 
                delta_t = ((self.fila.MaxService - self.fila.MinService) * nextRandom() + self.fila.MinService)
                self.tempo = tempo_global + delta_t

    def __lt__(self, other):
        return self.tempo < other.tempo

    def __str__(self):
        return f"Tipo: {self.tipo}, Tempo: {self.tempo:.4f}, Fila: {filas.index(self.fila) + 1}"

eventos = []

def nextRandom():
    global numero_previo, a, c, M, numeros_aleatorios_usados
    if numeros_aleatorios_usados >= qtd_numeros_aleatorios:
        return 1.0 # Evita gerar mais números que o permitido e força a parada
        
    numero_previo = (a * numero_previo + c) % M
    numeros_aleatorios_usados += 1
    return numero_previo / M

def loadYamlConfig(nome_arquivo):
    global a, c, M, seed, qtd_numeros_aleatorios, numero_previo
    try:
        with open(nome_arquivo, 'r') as file:
            data = yaml.safe_load(file)
            a = data.get('a', 0)
            c = data.get('c', 0)
            M = data.get('M', 0)
            seed = data.get('seed', 0.0)
            numero_previo = seed
            qtd_numeros_aleatorios = data.get('qtd_numeros_aleatorios', 0)

            # Carrega as Filas
            for fila_data in data.get('filas', []):
                # A sua lógica de carregamento YAML no Python era baseada em dicionário, não em linhas.
                # A capacidade infinita deve ser tratada no YAML (ex: 99999).
                fila = Fila(
                    fila_data['num_servidores'],
                    fila_data['capacidade_fila'],
                    fila_data['tempo_chegada_minimo'],
                    fila_data['tempo_chegada_maximo'],
                    fila_data['tempo_servico_minimo'],
                    fila_data['tempo_servico_maximo']
                )
                filas.append(fila)

            # Configura as Transições
            for transicao in data.get('transicoes', []):
                origem = transicao['origem'] - 1
                destino = transicao['destino']
                prob = transicao['probabilidade']
                if destino == "saida":
                    filas[origem].filas_conectadas.append(FilaEProbabilidade(None, prob, True))
                else:
                    destino_idx = int(destino) - 1
                    filas[origem].filas_conectadas.append(FilaEProbabilidade(filas[destino_idx], prob))
    except Exception as e:
        print(f"Erro ao carregar a configuração YAML: {e}")

def main():
    global eventos, tempo_global
    loadYamlConfig('input_simulador.yml')
    
    if not filas:
        print("Erro: Nenhuma fila foi carregada do arquivo de configuração.")
        return

    # CRÍTICO: Agenda o primeiro evento de chegada no tempo fixo de 2.0 (Fila 1)
    primeiro_evento = Evento('C', filas[0], tempo=2.0)
    heapq.heappush(eventos, primeiro_evento)

    while numeros_aleatorios_usados < qtd_numeros_aleatorios and eventos:
        e = heapq.heappop(eventos)
        
        # A simulação deve parar se o próximo evento for além do tempo limite do último aleatório usado.
        # No entanto, vamos confiar no 'nextRandom' para parar de gerar novos eventos e deixar o loop consumir os eventos remanescentes.
        
        if e.tipo == 'C' or e.tipo == 'A':
            e.fila.Chegada(e)
        elif e.tipo == 'P':
            e.fila.Passagem(e)
        elif e.tipo == 'S':
            e.fila.Saida(e)

    # Ao final, calcula o tempo restante no estado atual para cada fila
    for fila in filas:
        if fila.Timestamp < tempo_global:
            tempo_final_estado = tempo_global - fila.Timestamp
            fila.Times[fila.Customers] = fila.Times.get(fila.Customers, 0.0) + tempo_final_estado

    print(f"\n{'='*30}")
    print(f"SIMULAÇÃO FINALIZADA")
    print(f"{'='*30}\n")
    print(f"Tempo global da simulação: {tempo_global:.4f}")
    print(f"Números aleatórios usados: {numeros_aleatorios_usados}\n")
    
    for i, fila in enumerate(filas, start=1):
        print(f"----- Fila {i} (Servidores={fila.Server} / Capacidade={fila.Capacity}) -----")
        print(fila)

if __name__ == "__main__":
    main()