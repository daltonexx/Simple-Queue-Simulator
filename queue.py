import yaml
import heapq

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
        # Calcula o tempo decorrido desde o último evento nesta fila
        tempo_decorrido = e.tempo - self.Timestamp
        self.Times[self.Customers] = self.Times.get(self.Customers, 0.0) + tempo_decorrido
        
        # Atualiza o tempo do último evento e o tempo global
        self.Timestamp = e.tempo
        global tempo_global
        tempo_global = e.tempo

        if self.Customers < self.Capacity:
            self.Customers += 1
            if self.Customers <= self.Server:
                # Se há servidores livres, agenda uma passagem (P) ou saída (S)
                if len(self.filas_conectadas) > 0:
                    heapq.heappush(eventos, Evento('P', self))
                else:
                    heapq.heappush(eventos, Evento('S', self))
        else:
            self.Loss += 1
        
        # Se o evento foi uma chegada externa ('C'), agenda a próxima chegada externa
        if e.tipo == 'C':
            heapq.heappush(eventos, Evento('C', self))

    def Passagem(self, e):
        self.Saida(e) # Primeiro, processa a saída da fila atual
        
        # Determina para qual próxima fila o cliente vai
        probabilidade_passagem = nextRandom()
        acumulada = 0
        for rota in self.filas_conectadas:
            acumulada += rota.probabilidade
            if probabilidade_passagem < acumulada:
                if not rota.saida:
                    # Cria um novo evento de "chegada" na próxima fila
                    evento_chegada_proxima_fila = Evento('A', rota.fila, tempo=e.tempo) # 'A' para chegada interna
                    rota.fila.Chegada(evento_chegada_proxima_fila)
                # Se for 'saida', o cliente simplesmente vai embora.
                return

    def Saida(self, e):
        # Calcula o tempo decorrido desde o último evento nesta fila
        tempo_decorrido = e.tempo - self.Timestamp
        self.Times[self.Customers] = self.Times.get(self.Customers, 0.0) + tempo_decorrido
        
        # Atualiza o tempo do último evento e o tempo global
        self.Timestamp = e.tempo
        global tempo_global
        tempo_global = e.tempo

        self.Customers -= 1
        if self.Customers >= self.Server:
            # Se ainda há clientes na fila de espera, agenda o próximo serviço
            if len(self.filas_conectadas) != 0:
                heapq.heappush(eventos, Evento('P', self))
            else:
                heapq.heappush(eventos, Evento('S', self))

    def __str__(self):
        sb = f"Perda de clientes: {self.Loss}\n"
        
        # ## ALTERAÇÃO ##: Itera de 0 até a capacidade da fila, tornando a exibição dinâmica.
        for estado in range(self.Capacity + 1):
            tempo = self.Times.get(estado, 0.0)
            probabilidade = (tempo / tempo_global) * 100 if tempo_global > 0 else 0
            sb += f"Estado {estado}: tempo = {tempo:.4f} \t probabilidade = {probabilidade:.4f}%\n"
            
        return sb

class Evento:
    def __init__(self, tipo, fila_param=None, tempo=None):
        self.tipo = tipo
        self.fila = fila_param
        
        # ## ALTERAÇÃO ##: Prioriza o tempo passado como parâmetro. Se não for passado, calcula um novo.
        if tempo is not None:
            self.tempo = tempo
        else:
            if tipo == 'C':
                self.tempo = tempo_global + ((self.fila.MaxArrival - self.fila.MinArrival) * nextRandom() + self.fila.MinArrival)
            else: # 'S' ou 'P'
                self.tempo = tempo_global + ((self.fila.MaxService - self.fila.MinService) * nextRandom() + self.fila.MinService)

    def __lt__(self, other):
        return self.tempo < other.tempo

    def __str__(self):
        return f"Tipo: {self.tipo}, Tempo: {self.tempo:.4f}, Fila: {filas.index(self.fila) + 1}"

eventos = []

def nextRandom():
    global numero_previo, a, c, M, numeros_aleatorios_usados
    if numeros_aleatorios_usados >= qtd_numeros_aleatorios:
        return 1.0 # Evita gerar mais números que o permitido
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
            numero_previo = seed # Inicia o gerador com a semente
            qtd_numeros_aleatorios = data.get('qtd_numeros_aleatorios', 0)

            for fila_data in data.get('filas', []):
                fila = Fila(
                    fila_data['num_servidores'],
                    fila_data['capacidade_fila'],
                    fila_data['tempo_chegada_minimo'],
                    fila_data['tempo_chegada_maximo'],
                    fila_data['tempo_servico_minimo'],
                    fila_data['tempo_servico_maximo']
                )
                filas.append(fila)

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
        print(e)

def main():
    global eventos, tempo_global
    loadYamlConfig('input_simulador.yml')
    
    if not filas:
        print("Erro: Nenhuma fila foi carregada do arquivo de configuração.")
        return

    # ## ALTERAÇÃO ##: Cria o primeiro evento de chegada no tempo fixo de 1.5, conforme solicitado.
    primeiro_evento = Evento('C', filas[0], tempo=1.5)
    heapq.heappush(eventos, primeiro_evento)

    while numeros_aleatorios_usados < qtd_numeros_aleatorios and eventos:
        e = heapq.heappop(eventos)
        
        if e.tipo == 'C' or e.tipo == 'A':
            e.fila.Chegada(e)
        elif e.tipo == 'P':
            e.fila.Passagem(e)
        elif e.tipo == 'S':
            e.fila.Saida(e)

    # Ao final da simulação, calcula o tempo restante no estado atual para cada fila
    for fila in filas:
        if fila.Timestamp < tempo_global:
            tempo_final_estado = tempo_global - fila.Timestamp
            fila.Times[fila.Customers] = fila.Times.get(fila.Customers, 0.0) + tempo_final_estado

    print(f"SIMULAÇÃO FINALIZADA\n")
    print(f"Tempo global da simulação: {tempo_global:.4f}")
    print(f"Números aleatórios usados: {numeros_aleatorios_usados}\n")
    
    for i, fila in enumerate(filas, start=1):
        print(f"----- Fila {i} -----")
        print(fila)

if __name__ == "__main__":
    main()