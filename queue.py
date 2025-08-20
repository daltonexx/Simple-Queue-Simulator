import random
import heapq

# Usando o gerador de números aleatórios padrão do Python, que é mais robusto
def generate_interval(min_val, max_val):
    return random.uniform(min_val, max_val)

# Parâmetros da simulação
queue_capacity = 5
simulation_events = 100000

# Parâmetros de Chegada e Atendimento
arrival_min = 2
arrival_max = 5
service_min = 3
service_max = 5

def run_simulation(num_servers):
    # Dicionário para armazenar variáveis locais da simulação
    state = {
        'time': 0,
        'arrivals': 0,
        'departures': 0,
        'losses': 0,
        'total_waiting_time': 0,
        'queue': [],
        'servers_available': [True] * num_servers,
        'next_arrival_time': generate_interval(arrival_min, arrival_max),
        'future_events': [],  # Usado como uma fila de prioridade para eventos futuros
        'times_in_state': [0] * (queue_capacity + 1),
        'last_state_change_time': 0
    }

    # Função para agendar um evento futuro
    def schedule_event(event_time, event_type, *args):
        heapq.heappush(state['future_events'], (event_time, event_type, args))

    # Função para atualizar o tempo gasto em cada estado da fila
    def update_times_in_state():
        current_state = len(state['queue']) + (num_servers - state['servers_available'].count(True))
        time_elapsed = state['time'] - state['last_state_change_time']
        if current_state <= queue_capacity:
            state['times_in_state'][current_state] += time_elapsed
        state['last_state_change_time'] = state['time']

    # Agendar a primeira chegada
    schedule_event(state['next_arrival_time'], 'arrival')

    while state['departures'] < simulation_events:
        if not state['future_events']:
            break

        event_time, event_type, args = heapq.heappop(state['future_events'])
        
        # Avança o tempo da simulação para o tempo do próximo evento
        state['time'] = event_time
        
        # Atualiza os tempos nos estados da fila
        update_times_in_state()

        if event_type == 'arrival':
            state['arrivals'] += 1
            
            # Encontrar um servidor livre
            try:
                server_index = state['servers_available'].index(True)
            except ValueError:
                server_index = -1

            if server_index != -1:
                # Servidor livre, inicia o serviço imediatamente
                state['servers_available'][server_index] = False
                service_time = generate_interval(service_min, service_max)
                end_service_time = state['time'] + service_time
                state['total_waiting_time'] += 0 # Tempo de espera é 0
                
                # Agendar a saída do cliente
                schedule_event(end_service_time, 'departure', server_index)
            elif len(state['queue']) < queue_capacity:
                # Fila não está cheia, cliente entra na fila
                state['queue'].append(state['time'])
            else:
                # Fila cheia, cliente é perdido
                state['losses'] += 1
            
            # Agendar a próxima chegada
            next_arrival_time = state['time'] + generate_interval(arrival_min, arrival_max)
            schedule_event(next_arrival_time, 'arrival')

        elif event_type == 'departure':
            server_index = args[0]
            state['departures'] += 1
            
            if state['queue']:
                # Servidor atende o próximo cliente da fila
                arrival_time_from_queue = state['queue'].pop(0)
                service_time = generate_interval(service_min, service_max)
                end_service_time = state['time'] + service_time
                
                # O tempo de espera é a diferença entre o tempo atual (início do serviço) e o tempo de chegada
                state['total_waiting_time'] += state['time'] - arrival_time_from_queue
                
                # Agendar a saída do cliente
                schedule_event(end_service_time, 'departure', server_index)
            else:
                # Servidor fica ocioso
                state['servers_available'][server_index] = True

    return state

# Função para imprimir os resultados da simulação
def print_results(results, servers):
    print(f"--- Resultados para G/G/{servers}/{queue_capacity} ---")
    tempo_medio = results['total_waiting_time'] / results['departures'] if results['departures'] > 0 else 0
    loss_rate = results['losses'] / results['arrivals'] if results['arrivals'] > 0 else 0

    print(f"Total de chegadas: {results['arrivals']}")
    print(f"Total de saídas: {results['departures']}")
    print(f"Clientes perdidos: {results['losses']} ({loss_rate*100:.2f}%)")
    print(f"Tempo médio de espera: {tempo_medio:.4f}")
    print(f"Tempo total de simulação: {results['time']:.2f}")

    print("\nDistribuição de Probabilidade dos Estados da Fila:")
    for i in range(queue_capacity + 1):
        probability = results['times_in_state'][i] / results['time'] if results['time'] > 0 else 0
        print(f"Fila com {i} clientes: {probability * 100:.2f}%")

# Executar e imprimir para G/G/1/5
results_gg1 = run_simulation(1)
print_results(results_gg1, 1)

# Executar e imprimir para G/G/2/5
results_gg2 = run_simulation(2)
print("\n")
print_results(results_gg2, 2)