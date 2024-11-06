from socket import *
from threading import Thread, Lock
import random
from flask import Flask, request, jsonify
import requests
import json
app = Flask(__name__)
lock = Lock()
companhias = ["Companhia A", "Companhia B", "Companhia C"]

COMPANHIA = "C"
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

# Funções para gerar rotas e inicializar trechos
rotas = {}
trechos_comprados = {}

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
                        percurso.append((percurso_cidades[k], percurso_cidades[k+1], random.randint(2,5), COMPANHIA))
                    rotas[rota_nome].append(percurso)
    return rotas

def inicializar_trechos_comprados(rotas):
    return {rota: [[False] * len(trechos) for trechos in caminhos] for rota, caminhos in rotas.items()}

trechos_comprados = inicializar_trechos_comprados(rotas)

# API para verificar e reservar trechos entre companhias
@app.route("/api/check_trecho", methods=["GET"])
def check_trecho():
    rota = request.args.get("rota")
    trecho_idx = int(request.args.get("trecho_idx"))

    with lock:
        for caminho in rotas[rota]:
            trecho = caminho[trecho_idx]
            if trecho[2] > 0 and not trechos_comprados[rota][0][trecho_idx]:  # Considerando apenas o primeiro caminho
                return jsonify({"available": True})
    return jsonify({"available": False})

@app.route("/api/reservar_trecho", methods=["POST"])
def reservar_trecho():
    rota = request.json["rota"]
    trecho_idx = request.json["trecho_idx"]

    with lock:
        for caminho in rotas[rota]:
            trecho = caminho[trecho_idx]
            if trecho[2] > 0 and not trechos_comprados[rota][0][trecho_idx]:  # Considerando apenas o primeiro caminho
                trecho = (trecho[0], trecho[1], trecho[2] - 1, trecho[3])
                trechos_comprados[rota][0][trecho_idx] = True
                return jsonify({"reserved": True})
    return jsonify({"reserved": False})
# Função para listar todas as rotas disponíveis combinando com as outras companhias
def listar_rotas(con, rotas):
    enviar_mensagem(con, "Rotas disponíveis de todas as companhias:")

    # Dicionário para armazenar rotas unificadas (sem trechos)
    rotas_completas = set(rotas.keys())

    # Consultar rotas das outras companhias
    for companhia, url in OUTRAS_COMPANHIAS.items():
        try:
            # Consulta as rotas da outra companhia via API
            response = requests.get(f"{url}/rotas")
            response.raise_for_status()
            dados_companhia = response.json()

            # Adiciona as rotas da companhia ao conjunto
            rotas_completas.update(dados_companhia.keys())
        except requests.RequestException:
            enviar_mensagem(con, f"Erro ao obter rotas da companhia {companhia}")

    # Exibir as rotas disponíveis ao cliente (apenas nomes)
    rotas_completas = list(rotas_completas)
    for i, rota in enumerate(rotas_completas):
        enviar_mensagem(con, f"{i+1}. {rota}")

    enviar_mensagem(con, "Escolha uma rota pelo número para ver os trechos detalhados:")
    rota_idx = int(con.recv(1024).decode()) - 1
    rota_escolhida = rotas_completas[rota_idx]
    return rota_escolhida
# Função para listar rotas disponíveis para o cliente
#def listar_rotas(con, rotas):
#    enviar_mensagem(con, "Rotas disponíveis")
#    for i, rota in enumerate(rotas.keys()):
#        enviar_mensagem(con, f"{i+1}.{rota}")
#    enviar_mensagem(con, "Escolha uma rota pelo número:")
#    rota_idx = int(con.recv(1024).decode().strip()) - 1
#    return (rotas.keys())[rota_idx]

# Funções para consulta de trechos em outras companhias
def consultar_trecho_outra_companhia(rota, trecho_idx, companhia):
    url = OUTRAS_COMPANHIAS[companhia] + "/api/check_trecho"
    response = requests.get(url, params={"rota": rota, "trecho_idx": trecho_idx})
    return response.json()["available"]

def reservar_trecho_outra_companhia(rota, trecho_idx, companhia):
    url = OUTRAS_COMPANHIAS[companhia] + "/api/reservar_trecho"
    response = requests.post(url, json={"rota": rota, "trecho_idx": trecho_idx})
    return response.json()["reserved"]

# Função para enviar mensagem ao cliente
def enviar_mensagem(con, mensagem):
    con.send(f"{mensagem}\n".encode())

# Função para exibir trechos de todas as companhias
def listar_todos_trechos(con, rota_escolhida, rotas):
    enviar_mensagem(con, f"Trechos disponíveis para essa rota:{rota_escolhida}")
    #todos_trechos = rotas[rota_escolhida]

    for idx, caminho in enumerate(rotas[rota_escolhida]):
        enviar_mensagem(con, f"{idx+1}. Trecho {idx+1}:")
        for trecho in caminho:
            enviar_mensagem(con, f" - {trecho[0]} -> {trecho[1]} com {trecho[2]} passagens disponíveis, {trecho[3]}")
    
    enviar_mensagem(con, "Escolha um caminho pelo número:")
    caminho_idx = int(con.recv(1024).decode().strip()) - 1
    return rotas[rota_escolhida][caminho_idx], caminho_idx
    #if trecho_idx is not None:
    #    trecho = todos_trechos[0][trecho_idx]  # Considerando apenas o primeiro caminho
    #    companhia = trecho[3]
    #    if companhia == COMPANHIA:
    #        reservar_trecho_local(con, rota, trecho_idx)
    #    else:
    #        reservar_trecho_outra_companhia(con, rota, trecho_idx, companhia)

# Função para receber a escolha do cliente
def obter_escolha_cliente(con):
    """Recebe a escolha do cliente e converte para int, ou retorna None se inválido."""
    try:
        escolha = con.recv(1024).decode().strip()
        return int(escolha) - 1  # Decrementa 1 para manter a indexação correta
    except ValueError:
        return None

def verificar_disponibilidade():
    return

# Função para reservar um trecho localmente
def reservar_trecho_local(con, rota, trecho_idx):
    with lock:
        trecho = rotas[rota][0][trecho_idx]  # Considerando apenas o primeiro caminho
        if trecho[2] > 0:
            rotas[rota][0][trecho_idx] = (trecho[0], trecho[1], trecho[2] - 1, trecho[3])
            enviar_mensagem(con, "Compra realizada com sucesso!")
        else:
            enviar_mensagem(con, "Passagem indisponível.")

def handle_client(con, adr, rotas):
    print(f"Cliente conectado: {adr}")
    con.send("Bem-vindo ao sistema de compra de passagens!\n".encode())
    while True:
        rota_escolhida = listar_rotas(con, rotas)
        caminho_escolhido, caminho_idx = listar_todos_trechos(con, rota_escolhida, rotas)
        enviar_mensagem(con, "Verificando a disponibilidade dos trechos...")
        #with lock:
            
    # Exibir todos os trechos para a rota escolhida, com companhia indicada
    con.send("Trechos disponíveis para essa rota:\n".encode())
    todos_trechos = rotas[rota_escolhida]
    for idx, caminho in enumerate(todos_trechos):
        for trecho_idx, trecho in enumerate(caminho):
            origem, destino, _, companhia = trecho
            con.send(f"{idx + 1}.{trecho_idx + 1} - {origem} -> {destino} ({companhia})\n".encode())
    
    # Receber escolha de trecho do cliente
    trecho_idx = int(con.recv(1024).decode()) - 1

    # Determinar companhia do trecho escolhido
    trecho = todos_trechos[0][trecho_idx]  # Considerando apenas o primeiro caminho
    origem, destino, _, companhia = trecho

    # Reservar trecho localmente ou em outra companhia
    if companhia == COMPANHIA:
        # Reserva local
        reservar_trecho_local(con, rota_escolhida, trecho_idx)
    else:
        # Reserva em outra companhia
        reservado = reservar_trecho_outra_companhia(rota_escolhida, trecho_idx, companhia)
        if reservado:
            con.send("Compra realizada com sucesso!\n".encode())
        else:
            con.send("Passagem indisponível.\n".encode())

    con.close()
    print(f"Cliente desconectado: {adr}")

# Função principal do servidor
def main():
    host = '0.0.0.0'  # Escuta em todas as interfaces
    port = 10000
    rotas = gerar_rotas(cidades)
    server = socket(AF_INET, SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Servidor da Companhia {COMPANHIA} rodando...")

    while True:
        con, adr = server.accept()
        Thread(target=handle_client, args=(con, adr, rotas)).start()

if __name__ == "__main__":
    main()
