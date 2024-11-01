from socket import *
from threading import Thread, Lock
import random
import json
from flask import Flask, request, jsonify
import requests

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

# API para verificar e reservar trechos entre companhias
@app.route('/verificar_trecho', methods=['POST'])
def verificar_trecho():
    dados = request.json
    rota = dados['rota']
    caminho_idx = dados['caminho_idx']

    if rota in rotas and caminho_idx < len(rotas[rota]):
        caminho = rotas[rota][caminho_idx]
        disponibilidade = [trecho[2] > 0 for trecho in caminho]
        return jsonify({"disponivel": all(disponibilidade)})
    return jsonify({"erro": "Rota ou caminho inválido"}), 400

@app.route('/reservar_trecho', methods=['POST'])
def reservar_trecho():
    dados = request.json
    rota = dados['rota']
    caminho_idx = dados['caminho_idx']
    
    with lock:
        if rota in rotas and caminho_idx < len(rotas[rota]):
            for i, trecho in enumerate(rotas[rota][caminho_idx]):
                if trecho[2] <= 0:
                    return jsonify({"sucesso": False, "erro": "Trecho indisponível"})
                rotas[rota][caminho_idx][i] = (trecho[0], trecho[1], trecho[2] - 1)
            return jsonify({"sucesso": True})
    return jsonify({"sucesso": False, "erro": "Rota ou caminho inválido"}), 400

# Função para consultar trecho em servidor conveniado
def consultar_trecho_externo(rota, caminho_idx, companhia_url):
    resposta = requests.post(f"{companhia_url}/verificar_trecho", json={"rota": rota, "caminho_idx": caminho_idx})
    return resposta.json().get("disponivel", False)

# Função para reservar trecho em servidor conveniado
def reservar_trecho_externo(rota, caminho_idx, companhia_url):
    resposta = requests.post(f"{companhia_url}/reservar_trecho", json={"rota": rota, "caminho_idx": caminho_idx})
    return resposta.json().get("sucesso", False)

# Função para processar a compra de trechos
def handle_client(con, addr):
    while True:
        # Realizar processo de compra semelhante ao código anterior, mas agora considerando conveniadas
        # Exemplo de chamada para verificar e reservar trecho em outro servidor:
        for nome, url in CONVENIADAS.items():
            if consultar_trecho_externo("Belém-Fortaleza", 0, url):
                if reservar_trecho_externo("Belém-Fortaleza", 0, url):
                    con.send("Trecho reservado com sucesso!".encode())
                else:
                    con.send("Erro ao reservar trecho.".encode())

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
