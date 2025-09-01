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
        # Ajustar para evitar tempos negativos
        tempo_chegada = e.tempo - self.Timestamp
        if tempo_chegada < 0:
            tempo_chegada = 0  # Evitar valores negativos no tempo

        self.Times[self.Customers] = self.Times.get(self.Customers, 0.0) + tempo_chegada
        self.Timestamp = e.tempo
        global tempo_global
        tempo_global = e.tempo

        if self.Customers < self.Capacity:
            self.Customers += 1
            if self.Customers <= self.Server:
                if len(self.filas_conectadas) > 0:
                    eventos.append(Evento('P', self))
                else:
                    eventos.append(Evento('S', self))
        else:
            self.Loss += 1
        if e.tipo == 'C':
            eventos.append(Evento('C', self))

    def Passagem(self, e):
        self.Saida(e)
        probabilidade_passagem = nextRandom()
        acumulada = 0
        for fila in self.filas_conectadas:
            acumulada += fila.probabilidade
            if probabilidade_passagem < acumulada:
                if not fila.saida:
                    e.fila = fila.fila
                    e.fila.Chegada(e)
                return
        ultima = self.filas_conectadas[-1]
        if not ultima.saida:
            e.fila = ultima.fila
            e.fila.Chegada(e)

    def Saida(self, e):
        # Ajustar para evitar tempos negativos
        tempo_saida = e.tempo - self.Timestamp
        if tempo_saida < 0:
            tempo_saida = 0  # Evitar valores negativos no tempo

        self.Times[self.Customers] = self.Times.get(self.Customers, 0.0) + tempo_saida
        self.Timestamp = e.tempo
        global tempo_global
        tempo_global = e.tempo
        self.Customers -= 1
        if self.Customers >= self.Server:
            if len(self.filas_conectadas) != 0:
                eventos.append(Evento('P', self))
            else:
                eventos.append(Evento('S', self))

    def __str__(self):
        sb = f"Perda de clientes: {self.Loss}\n"
        
        # Exibir todos os 6 estados (de 0 a 5), mesmo que alguns tenham 0% de probabilidade
        for estado in range(6):  # Agora são 6 estados (de 0 a 5)
            tempo = self.Times.get(estado, 0.0)  # Garantir que todos os 6 estados sejam exibidos
            probabilidade = (tempo / tempo_global) * 100 if tempo_global > 0 else 0
            sb += f"Estado {estado}: tempo = {tempo:.4f} \t probabilidade = {probabilidade:.4f}%\n"
        
        return sb

class Evento:
    def __init__(self, tipo, fila_param=None, tempo=None):
        self.tipo = tipo
        self.fila = fila_param
        if tipo == 'C':
            self.tempo = tempo_global + ((self.fila.MaxArrival - self.fila.MinArrival) * nextRandom() + self.fila.MinArrival)
        else:
            self.tempo = tempo_global + ((self.fila.MaxService - self.fila.MinService) * nextRandom() + self.fila.MinService)

    def __lt__(self, other):
        """Método para comparar os eventos com base no tempo."""
        return self.tempo < other.tempo

    def __str__(self):
        return f"{self.tipo} {self.tempo}"

eventos = []

def nextRandom():
    global numero_previo, a, c, M, numeros_aleatorios_usados
    numero_previo = (a * numero_previo + c) % M
    numeros_aleatorios_usados += 1
    return numero_previo / M

def loadYamlConfig(nome_arquivo):
    global a, c, M, seed, qtd_numeros_aleatorios
    try:
        with open(nome_arquivo, 'r') as file:
            data = yaml.safe_load(file)
            a = data.get('a', 0)
            c = data.get('c', 0)
            M = data.get('M', 0)
            seed = data.get('seed', 0.0)
            qtd_numeros_aleatorios = data.get('qtd_numeros_aleatorios', 0)

            for fila_data in data.get('filas', []):
                tempo_chegada_minimo = fila_data['tempo_chegada_minimo']
                tempo_chegada_maximo = fila_data['tempo_chegada_maximo']
                tempo_servico_minimo = fila_data['tempo_servico_minimo']
                tempo_servico_maximo = fila_data['tempo_servico_maximo']
                num_servidores = fila_data['num_servidores']
                capacidade_fila = fila_data['capacidade_fila']
                
                # Tratamento para capacidade infinita ou string numérica
                if capacidade_fila == "infinito":
                    capacidade_fila = float('inf')  # Use infinito para capacidade ilimitada
                else:
                    capacidade_fila = int(capacidade_fila)  # Converta para inteiro se for numérico
                
                fila = Fila(num_servidores, capacidade_fila, tempo_chegada_minimo, tempo_chegada_maximo,
                            tempo_servico_minimo, tempo_servico_maximo)
                filas.append(fila)

            for transicao in data.get('transicoes', []):
                origem = transicao['origem'] - 1
                destino = transicao['destino']
                prob = transicao['probabilidade']
                if destino == "saida":
                    filas[origem].filas_conectadas.append(FilaEProbabilidade(None, prob, True))
                else:
                    destino = int(destino) - 1
                    filas[origem].filas_conectadas.append(FilaEProbabilidade(filas[destino], prob))

            for fila in filas:
                fila.filas_conectadas.sort(key=lambda f: f.probabilidade)
    except Exception as e:
        print(e)

def main():
    global eventos
    loadYamlConfig('input_simulador.yml')
    print("Filas carregadas:", filas)
    if not filas:
        print("Erro: Não há filas carregadas!")
        return
    numero_previo = seed
    eventos.append(Evento('C', filas[0], 2))

    while numeros_aleatorios_usados < qtd_numeros_aleatorios:
        e = heapq.heappop(eventos)
        if e.tipo == 'C':
            e.fila.Chegada(e)
        elif e.tipo == 'P':
            e.fila.Passagem(e)
        elif e.tipo == 'S':
            e.fila.Saida(e)

    print(f"Tempo global da simulação: {tempo_global:.4f}")
    for i, fila in enumerate(filas, start=1):
        fila.Times[fila.Customers] = fila.Times.get(fila.Customers, 0.0) + (tempo_global - fila.Timestamp)
        print(f"Fila {i}:")
        print(fila)

if __name__ == "__main__":
    main()
