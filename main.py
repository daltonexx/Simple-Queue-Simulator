import random

# Função para gerar números aleatórios usando o Método Congruente Linear
def NextRandom(a, c, M, seed):
    global last_value
    last_value = (a * last_value + c) % M
    return last_value / M  # Retorna número normalizado entre 0 e 1

# Função para gerar intervalos aleatórios entre os limites
def generate_interval(min_val, max_val):
    return min_val + (max_val - min_val) * NextRandom(a, c, M, seed)

# Parâmetros para o gerador congruente linear
a = 1664525
c = 1013904223
M = 2**32
seed = 123456
last_value = seed

# Configurações da fila
queue_capacity = 5  # Capacidade máxima da fila
simulation_time = 100000  # Número de eventos a serem simulados

# Parâmetros de Chegada e Atendimento
arrival_min = 2  # Mínimo para tempo de chegada
arrival_max = 5  # Máximo para tempo de chegada
service_min = 3  # Mínimo para tempo de atendimento
service_max = 5  # Máximo para tempo de atendimento

# Contadores e variáveis auxiliares
time = 0  # Tempo da simulação
arrivals = 0  # Contador de clientes que chegaram
departures = 0  # Contador de clientes que saíram
losses = 0  # Contador de perda de clientes
total_waiting_time = 0  # Tempo total de espera

# Fila e servidores
queue = []  # Fila de clientes
servers = 1  # Número de servidores, pode ser 1 ou 2
clients_serving = [None] * servers  # Status de servidores (None = o servidor está livre)

# Função para processar chegada de cliente
def arrival():
    global arrivals, losses
    arrivals += 1
    if len(queue) < queue_capacity:  # Se houver espaço na fila
        queue.append(time)
    else:
        losses += 1  # Cliente perdido se a fila estiver cheia

# Função para processar saída de cliente
def departure():
    global departures, total_waiting_time
    for i in range(servers):
        if clients_serving[i] is not None:
            # O tempo de espera é calculado a partir do tempo de chegada (clients_serving[i] guarda o tempo de chegada)
            arrival_time = clients_serving[i]  # O tempo de chegada é o valor armazenado na fila
            # Verificar se o tempo atual não é menor que o tempo de chegada
            if time < arrival_time:
                print("ERRO: O tempo atual é menor que o tempo de chegada. Corrija a lógica de chegada!")
                break
            
            # Calcular o tempo de espera
            waiting_time = time - arrival_time  # Tempo de espera é a diferença entre o tempo atual e o tempo de chegada
            
            # Atualizar o total de tempo de espera
            total_waiting_time += waiting_time
            departures += 1
            
            clients_serving[i] = None  # Liberar o servidor
            break

# Função para atender clientes, escolhendo quem vai ser atendido
def serve():
    global clients_serving
    for i in range(servers):
        if clients_serving[i] is None and len(queue) > 0:
            client_arrival_time = queue.pop(0)
            service_time = generate_interval(service_min, service_max)
            clients_serving[i] = time + service_time  # Atribui tempo de serviço ao servidor

# Função para rodar a simulação
def run_simulation():
    global time
    while time < simulation_time:
        event_type = NextRandom(a, c, M, seed)  # Gera um número aleatório para decidir evento

        if event_type < 0.5:  # 50% de chance de chegar um cliente
            arrival()
        else:  # Caso contrário, um cliente vai sair
            departure()

        serve()  # Atende os clientes se possível
        time += 1  # Avança o tempo

# Função para imprimir os resultados da simulação
def print_results():
    print(f"Total de chegadas: {arrivals}")
    print(f"Total de saídas: {departures}")
    print(f"Clientes perdidos: {losses}")
    print(f"Tempo médio de espera: {total_waiting_time / departures if departures > 0 else 0}")
    print(f"Tempo total de simulação: {time}")

# Executar a simulação
run_simulation()
print_results()
