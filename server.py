from socket import *
from threading import Thread, Lock
import random
import json
from flask import Flask, request, jsonify
import requests
import time

# Endereços IP dos servidores VENDEPASS das companhias conveniadas
CONVENIADAS = {
    'Companhia A': 'http://172.16.112.1:5000',
    'Companhia B': 'http://172.16.112.2:5000',
    'Companhia C': 'http://172.16.112.3:5000'
}

app = Flask(__name__)
lock = Lock()
cidades = ["Belém", "Fortaleza", "Brasília", "São Paulo", "Curitiba", 
           "Rio de Janeiro", "Porto Alegre", "Salvador", "Manaus", "Recife"]

rotas = {}
trechos_comprados = {}
timestamp = int(time.time())
esperando_resposta = {}  # Controla respostas para requisições Ricart-Agrawala
fila_pedidos = []  # Armazena pedidos de outros servidores para acessar a seção crítica

# Gerar rotas
def gerar_rotas(cidades):
    global rotas
    rotas = {}
    for i in range(len(cidades)):
        for j in range(len(cidades)):
            if i != j:
                rota_nome = f"{cidades[i]}-{cidades[j]}"
                rotas[rota_nome] = []
                num_caminhos = random.randint(1, 3)
                for _ in range(num_caminhos):
                    caminho = []
                    cidades_intermediarias = random.sample(cidades[:i] + cidades[i+1:], random.randint(1, 3))
                    caminho_cidades = [cidades[i]] + cidades_intermediarias + [cidades[j]]
                    for k in range(len(caminho_cidades) - 1):
                        caminho.append((caminho_cidades[k], caminho_cidades[k+1], random.randint(2, 5)))
                    rotas[rota_nome].append(caminho)

# Inicializar trechos
def inicializar_trechos_comprados():
    global trechos_comprados
    trechos_comprados = {rota: [[False] * len(trechos) for trechos in caminhos] for rota, caminhos in rotas.items()}

# Consultar rotas disponíveis nas conveniadas
def consultar_rotas_conveniada(rota_escolhida, url_conveniada):
    try:
        response = requests.get(f"{url_conveniada}/consultar_rotas/{rota_escolhida}")
        if response.status_code == 200:
            return response.json().get("caminhos", [])
        else:
            print(f"Erro ao consultar {url_conveniada}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro ao se comunicar com {url_conveniada}: {e}")
        return []

# Função para reservar um trecho em uma companhia conveniada
def reservar_trecho_externo(rota_escolhida, caminho_idx, url_conveniada):
    try:
        response = requests.post(f"{url_conveniada}/reservar_trecho", json={
            "rota": rota_escolhida,
            "caminho_idx": caminho_idx
        })
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao reservar trecho em {url_conveniada}: {e}")
        return False

# Funções de Ricart-Agrawala

# Envia requisições a outros servidores para acesso à seção crítica
def requisitar_acesso(rota, caminho_idx):
    global timestamp, esperando_resposta
    timestamp += 1
    esperando_resposta[rota] = {url: False for url in CONVENIADAS.values()}
    for url in CONVENIADAS.values():
        try:
            requests.post(f"{url}/pedido_acesso", json={
                "rota": rota,
                "caminho_idx": caminho_idx,
                "timestamp": timestamp
            })
        except Exception as e:
            print(f"Erro ao enviar requisição para {url}: {e}")

# Processa a resposta de servidores concedendo acesso à seção crítica
@app.route('/responder_pedido', methods=['POST'])
def responder_pedido():
    dados = request.json
    rota = dados["rota"]
    caminho_idx = dados["caminho_idx"]
    global fila_pedidos

    fila_pedidos.append((rota, caminho_idx))
    return jsonify({"sucesso": True})

# Processa requisições de outros servidores para acessar seção crítica
@app.route('/pedido_acesso', methods=['POST'])
def pedido_acesso():
    dados = request.json
    rota = dados["rota"]
    caminho_idx = dados["caminho_idx"]
    timestamp_pedido = dados["timestamp"]

    if timestamp_pedido < timestamp or not fila_pedidos:
        return jsonify({"resposta": "ok"})

    while fila_pedidos:
        requisicao_atual = fila_pedidos.pop(0)
        if requisicao_atual[0] == rota and requisicao_atual[1] == caminho_idx:
            timestamp += 1
            return jsonify({"resposta": "ok"})

    return jsonify({"erro": "Falha ao processar pedido"}), 500

# Função para reservar um trecho localmente
def reservar_trecho_local(rota_escolhida, caminho_idx):
    caminho = rotas[rota_escolhida][caminho_idx]
    for i, trecho in enumerate(caminho):
        origem, destino, passagens = trecho
        rotas[rota_escolhida][caminho_idx][i] = (origem, destino, passagens - 1)

# Função para processar a compra de trechos com consulta a todas as companhias
def handle_client(con, addr):
    try:
        # Enviar mensagem de boas-vindas ao cliente
        con.send(json.dumps({"mensagem": "Bem-vindo ao sistema VENDEPASS!", "rotas": list(rotas.keys())}).encode())

        # Receber escolha da rota do cliente
        dados = json.loads(con.recv(1024).decode())
        rota_escolhida = dados.get("rota")

        if rota_escolhida not in rotas:
            con.send(json.dumps({"erro": "Rota inválida!"}).encode())
            return

        # Montar lista de caminhos com as rotas disponíveis na companhia atual
        caminhos_disponiveis = [{"caminho": i, "trechos": [(trecho[0], trecho[1], trecho[2], "Companhia Atual")]}
                                for i, caminho in enumerate(rotas[rota_escolhida])]

        # Consultar rotas nas conveniadas
        for nome, url in CONVENIADAS.items():
            trechos_conveniados = consultar_rotas_conveniada(rota_escolhida, url)
            if trechos_conveniados:
                for caminho_idx, caminho in enumerate(trechos_conveniados):
                    caminhos_disponiveis.append({
                        "caminho": f"{caminho_idx} (Conveniadas)", 
                        "trechos": [(trecho[0], trecho[1], trecho[2], nome) for trecho in caminho]
                    })

        # Enviar lista consolidada de caminhos e companhias para o cliente
        con.send(json.dumps({"mensagem": "Escolha um caminho", "caminhos": caminhos_disponiveis}).encode())

        # Receber escolha do caminho do cliente
        dados = json.loads(con.recv(1024).decode())
        caminho_idx = dados.get("caminho")

        # Requisitar acesso para modificar trecho usando Ricart-Agrawala
        requisitar_acesso(rota_escolhida, caminho_idx)

        # Reserva de trechos na companhia correta
        for trecho in caminhos_disponiveis[caminho_idx]["trechos"]:
            origem, destino, passagens, companhia = trecho
            if companhia == "Companhia Atual":
                with lock:
                    reservar_trecho_local(rota_escolhida, caminho_idx)
            else:
                url_conveniada = CONVENIADAS[companhia]
                if not reservar_trecho_externo(rota_escolhida, caminho_idx, url_conveniada):
                    con.send(json.dumps({"erro": f"Erro ao reservar trecho {origem}-{destino} na {companhia}."}).encode())
                    return

        # Confirmação da reserva ao cliente
        con.send(json.dumps({"sucesso": "Reserva completa com todos os trechos disponíveis!"}).encode())

    except Exception as e:
        con.send(json.dumps({"erro": str(e)}).encode())
    finally:
        con.close()

# Configuração do socket para o cliente
def iniciar_socket():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 10000))
    server_socket.listen(5)
    print("Servidor de passagens aéreas rodando...")

    while True:
        con, addr = server_socket.accept()
        Thread(target=handle_client, args=(con, addr)).start()

if __name__ == "__main__":
    gerar_rotas(cidades)
    inicializar_trechos_comprados()
    Thread(target=iniciar_socket).start()
    app.run(host="0.0.0.0", port=5000)