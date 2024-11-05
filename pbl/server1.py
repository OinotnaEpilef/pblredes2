from socket import *
from threading import Thread, Lock
import random
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)
lock = Lock()
companhias = ["Companhia A", "Companhia B", "Companhia C"]

# Identificador da companhia e IPs das outras companhias
COMPANHIA = "C"  # Altere para "A", "B", ou "C" dependendo da companhia
companhias = ["Companhia A", "Companhia B", "Companhia C"]
OUTRAS_COMPANHIAS = {
    "A": "http://172.16.112.1:5000",
    "B": "http://172.16.112.2:5000",
    "C": "http://172.16.112.3:5000"
}
# Remover a companhia local do dicionário para evitar consultas a si mesma
OUTRAS_COMPANHIAS.pop(COMPANHIA, None)

# Lista de cidades e geração de rotas como antes
cidades = ["Belém", "Fortaleza", "Brasília", "São Paulo", "Curitiba", 
           "Rio de Janeiro", "Porto Alegre", "Salvador", "Manaus", "Recife"]

# Funções para gerar rotas e inicializar trechos de forma semelhante à original
rotas = {}  # Será inicializada como antes
trechos_comprados = {}  # Estado dos trechos será inicializado com a função 'inicializar_trechos_comprados'

# Funções auxiliares para inicializar rotas e trechos
def gerar_rotas(cidades):
    rotas = {}
    for i in range(len(cidades)):
        for j in range(len(cidades)):
            if i != j:
                rota_nome = f"{cidades[i]}-{cidades[j]}"
                rotas[rota_nome] = []
                num_percursos = random.randint(1, 3)
                for _ in range(num_percursos):
                    percurso = []
                    cidades_intermediarias = random.sample(cidades[:i] + cidades[i+1:], random.randint(1, 3))
                    percurso_cidades = [cidades[i]] + cidades_intermediarias + [cidades[j]]
                    for k in range(len(percurso_cidades) - 1):
                        # Cada trecho agora inclui a companhia responsável
                        trecho = (
                            percurso_cidades[k], 
                            percurso_cidades[k+1], 
                            random.randint(2, 5),  # número de passagens
                            random.choice(companhias)  # companhia responsável
                        )
                        percurso.append(trecho)
                    rotas[rota_nome].append(percurso)
    return rotas

def inicializar_trechos_comprados(rotas):
    return {rota: [[False] * len(trechos) for trechos in caminhos] for rota, caminhos in rotas.items()}

rotas = gerar_rotas(cidades)
trechos_comprados = inicializar_trechos_comprados(rotas)

# API para verificar e reservar trechos entre companhias
@app.route("/api/check_trecho", methods=["GET"])
def check_trecho():
    rota = request.args.get("rota")
    caminho_idx = int(request.args.get("caminho_idx"))
    trecho_idx = int(request.args.get("trecho_idx"))

    with lock:
        trecho = rotas[rota][caminho_idx][trecho_idx]
        if trecho[2] > 0 and not trechos_comprados[rota][caminho_idx][trecho_idx]:
            return jsonify({"available": True})
    return jsonify({"available": False})

@app.route("/api/reservar_trecho", methods=["POST"])
def reservar_trecho():
    rota = request.json["rota"]
    caminho_idx = request.json["caminho_idx"]
    trecho_idx = request.json["trecho_idx"]

    with lock:
        trecho = rotas[rota][caminho_idx][trecho_idx]
        if trecho[2] > 0 and not trechos_comprados[rota][caminho_idx][trecho_idx]:
            trecho = (trecho[0], trecho[1], trecho[2] - 1, trecho[3])
            trechos_comprados[rota][caminho_idx][trecho_idx] = True
            return jsonify({"reserved": True})
    return jsonify({"reserved": False})

# Funções para consulta de trechos em outras companhias
def consultar_trecho_outra_companhia(rota, caminho_idx, trecho_idx, companhia):
    url = OUTRAS_COMPANHIAS[companhia] + "/api/check_trecho"
    response = requests.get(url, params={"rota": rota, "caminho_idx": caminho_idx, "trecho_idx": trecho_idx})
    return response.json()["available"]

def reservar_trecho_outra_companhia(rota, caminho_idx, trecho_idx, companhia):
    url = OUTRAS_COMPANHIAS[companhia] + "/api/reservar_trecho"
    response = requests.post(url, json={"rota": rota, "caminho_idx": caminho_idx, "trecho_idx": trecho_idx})
    return response.json()["reserved"]

#função para enviar mensagem ao cliente
def enviar_mensagem(con, mensagem):
    """Envia uma mensagem ao cliente."""
    con.send(f"{mensagem}\n".encode())

# Função para exibir trechos de todas as companhias
def listar_todos_caminhos(con, rota):
    enviar_mensagem(con, "Caminhos disponíveis para essa rota:")
    todos_caminhos = rotas[rota]

    for idx, caminho in enumerate(todos_caminhos):
        for trecho_idx, trecho in enumerate(caminho):
            origem, destino, _, companhia = trecho
            enviar_mensagem(con, f"{idx + 1}.{trecho_idx + 1} - {origem} -> {destino} ({companhia})")
    
    # Depois de listar os trechos, o cliente escolhe
    caminho_idx, trecho_idx, companhia = obter_escolha_cliente(con)
    if companhia == COMPANHIA:
        reservar_trecho_local(con, rota, caminho_idx, trecho_idx)
    else:
        reservar_trecho_outra_companhia(con, rota, caminho_idx, trecho_idx, companhia)

#função para receber a escolha do cliente
def obter_escolha_cliente(con):
    """Recebe a escolha do cliente e converte para int, ou retorna None se inválido."""
    try:
        escolha = con.recv(1024).decode().strip()
        return int(escolha)
    except ValueError:
        return None

# Função para reservar um trecho localmente
def reservar_trecho_local(con, rota, caminho_idx, trecho_idx):
    with lock:
        trecho = rotas[rota][caminho_idx][trecho_idx]
        if trecho[2] > 0:
            rotas[rota][caminho_idx][trecho_idx] = (trecho[0], trecho[1], trecho[2] - 1, trecho[3])
            enviar_mensagem(con, "Compra realizada com sucesso!")
        else:
            enviar_mensagem(con, "Passagem indisponível.")

def handle_client(con, adr):
    print(f"Cliente conectado: {adr}")
    con.send("Bem-vindo ao sistema de compra de passagens!\n".encode())
    
    # Listar rotas disponíveis
    con.send("Rotas disponíveis:\n".encode())
    for idx, rota in enumerate(rotas.keys()):
        con.send(f"{idx + 1} - {rota}\n".encode())
    
    # Receber escolha da rota do cliente
    rota_idx = int(con.recv(1024).decode()) - 1
    rota_escolhida = list(rotas.keys())[rota_idx]

    # Exibir todos os caminhos para a rota escolhida, com companhia indicada
    con.send("Caminhos disponíveis para essa rota:\n".encode())
    todos_caminhos = rotas[rota_escolhida]
    for idx, caminho in enumerate(todos_caminhos):
        for trecho_idx, trecho in enumerate(caminho):
            origem, destino, _, companhia = trecho
            con.send(f"{idx + 1}.{trecho_idx + 1} - {origem} -> {destino} ({companhia})\n".encode())
    
    # Receber escolha de caminho e trecho do cliente
    caminho_idx = int(con.recv(1024).decode()) - 1
    trecho_idx = int(con.recv(1024).decode()) - 1

    # Determinar companhia do trecho escolhido
    trecho = todos_caminhos[caminho_idx][trecho_idx]
    origem, destino, _, companhia = trecho

    # Reservar trecho localmente ou em outra companhia
    if companhia == COMPANHIA:
        # Reserva local
        reservar_trecho_local(con, rota_escolhida, caminho_idx, trecho_idx)
    else:
        # Reserva em outra companhia
        reservado = reservar_trecho_outra_companhia(rota_escolhida, caminho_idx, trecho_idx, companhia)
        if reservado:
            con.send("Compra realizada com sucesso!\n".encode())
        else:
            con.send("Passagem indisponível.\n".encode())

    con.close()
    print(f"Conexão encerrada com {adr}")


# Função principal do servidor
def main():
    host = '0.0.0.0'  # Escuta em todas as interfaces
    port = 10000

    server = socket(AF_INET, SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Servidor da Companhia {COMPANHIA} rodando...")

    while True:
        con, adr = server.accept()
        Thread(target=handle_client, args=(con, adr)).start()

if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()
    main()
