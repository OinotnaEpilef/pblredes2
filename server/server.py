from socket import *
from threading import Thread, Lock
import random
from flask import Flask, request, jsonify
import requests
client_ID = 0
pendentes = {}
sequencial = 0
app = Flask(__name__)
lock = Lock()
companhias = ["Companhia A", "Companhia B", "Companhia C"]
rotas = {}
cidades = ["Belém", "Fortaleza", "Brasília", "São Paulo", "Curitiba", 
           "Rio de Janeiro", "Porto Alegre", "Salvador", "Manaus", "Recife"]
COMPANHIA = "C"
OUTRAS_COMPANHIAS = {
    "A": "http://172.16.103.1:43342",
    "B": "http://172.16.103.2:43342",
    "C": "http://172.16.103.3:43342"
}
# Remover a companhia local do dicionário para evitar consultas a si mesma
OUTRAS_COMPANHIAS.pop(COMPANHIA, None)

def gerar_rotas(cidades):
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

#chama a solicitação de acesso a região crítica
def solicitar_permissao(cliente_id, companhias):
    """
    Solicita permissão a todos os servidores para garantir que o cliente tenha acesso
    exclusivo para a compra.
    """
    for companhia in companhias:
        url = f"http://{companhia}.com/solicitar_acesso"
        response = requests.post(url, json={"cliente_id": cliente_id})
        print(response.json())

# Solicitação de acesso à seção crítica
@app.route("/solicitar_acesso", methods=["POST"])
def solicitar_acesso():
    global sequencial
    cliente_id = request.args.get("cliente_id")

    if cliente_id not in pendentes:
        pendentes[cliente_id] = []

    pendentes[cliente_id].append({
        "sequencial": sequencial
    })
    sequencial += 1

    # Envia a solicitação para todas as outras companhias
    for companhia, url in OUTRAS_COMPANHIAS.items():
        try:
            response = requests.post(f"{url}/resposta_solicitacao", json={"cliente_id": cliente_id, "sequencial": sequencial})
            response.raise_for_status()
        except requests.RequestException:
            return jsonify({"error": f"Erro ao solicitar permissão para a companhia {companhia}"}), 500
    return jsonify({"sucesso": True})

# Resposta da solicitação de acesso à seção crítica
@app.route("/resposta_solicitacao", methods=["POST"])
def resposta_solicitacao():
    cliente_id = request.json.get("cliente_id")
    sequencial = request.json.get("sequencial")

    if cliente_id not in pendentes:
        return jsonify({"error": "Cliente não encontrado"}), 404
    
    # Verifica se o pedido está em ordem
    if sequencial > pendentes[cliente_id][0]["sequencial"]:
        pendentes[cliente_id].append({"sequencial": sequencial})
        return jsonify({"sucesso": True})
    return jsonify({"sucesso": False})
#api para verificar disponibilidade de passagens
@app.route("/verificar_disponibilidade", methods=["GET"])
def verificar_disponibilidade():
    origem = request.args.get("origem")
    destino = request.args.get("destino")
    
    if not origem or not destino:
        return jsonify({"error": "Parâmetros 'origem' e 'destino' são necessários"}), 400
    
    # Percorre as rotas para encontrar o trecho com origem e destino solicitados
    for rota in rotas.values():
        for trecho in rota:
            if trecho[0] == origem and trecho[1] == destino:
                if trecho[2] > 0:
                    passagens_disponiveis = trecho[2]
                    return jsonify({"passagens_disponiveis": passagens_disponiveis})
    # Se não encontrar o trecho, indica que o trecho não existe ou está indisponível
    return jsonify({"error": "Trecho não encontrado ou indisponível"}), 404

#api para comprar passagens
@app.route("/realizar_compra", methods=["POST"])
def verificar_disponibilidade():
    origem = request.args.get("origem")
    destino = request.args.get("destino")
    
    if not origem or not destino:
        return jsonify({"error": "Parâmetros 'origem' e 'destino' são necessários"}), 400
    
    # Percorre as rotas para encontrar o trecho com origem e destino solicitados
    for rota in rotas.values():
        for trecho in rota:
            if trecho[0] == origem and trecho[1] == destino:
                trecho[2] -=1
    # Se não encontrar o trecho, indica que o trecho não existe ou está indisponível
    return jsonify({"error": "Trecho não encontrado ou indisponível"}), 404

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
    companhia = trecho[3]
    return rotas[rota_escolhida][caminho_idx], companhia

# Percorre os trechos e verifica a disponibilidade
def verificar_disponibilidade(caminho, companhia_atual):
    for trecho in caminho:
        origem, destino, passagens_disponiveis, companhia = trecho
        if companhia == companhia_atual:
            # Verifica localmente se o trecho é da companhia atual
            if passagens_disponiveis <= 0:
                return False  # Sem passagens disponíveis localmente
        else:
            # Consulta a companhia remota para verificar a disponibilidade
            match trecho[3]:
                case "Companhia A":
                    url_companhia = "http://172.16.103.1:43342"
                case "Companhia B":
                    url_companhia = "http://172.16.103.2:43342"
                case "Companhia C":
                    url_companhia = "http://172.16.103.3:43342"
            try:
                response = requests.get(f"{url_companhia}/verificar_disponibilidade", params={"origem": origem, "destino": destino})
                response.raise_for_status()
                disponivel = response.json().get("disponivel", False)
                if not disponivel:
                    return False  # Se o trecho não tiver passagens, retorna False
            except requests.RequestException as e:
                print(f"Erro ao verificar a disponibilidade no servidor da companhia {companhia}: {e}")
                return False  # Em caso de erro, assume indisponibilidade
    return True  # Se todos os trechos tiverem passagens disponíveis, retorna True

#faz a compra dos trechos
def realizar_compra(caminho, companhia_atual):
    for i, trecho in enumerate(caminho):
        origem, destino, passagens_disponiveis, companhia = trecho
        
        if companhia == companhia_atual:
            # Compra local: decrementa o número de passagens
            caminho[i] = (origem, destino, passagens_disponiveis - 1, companhia)
        else:
            # Compra remota: realiza uma requisição para decrementar no servidor da outra companhia
            match trecho[3]:
                case "Companhia A":
                    url_companhia = "http://172.16.103.1:43342"
                case "Companhia B":
                    url_companhia = "http://172.16.103.2:43342"
                case "Companhia C":
                    url_companhia = "http://172.16.103.3:43342"
            try:
                response = requests.post(f"{url_companhia}/realizar_compra", json={"origem": origem, "destino": destino})
                response.raise_for_status()  # Confirma sucesso da requisição
                sucesso = response.json().get("sucesso", False)
                if not sucesso:
                    print(f"Falha ao realizar a compra do trecho {origem} -> {destino} na companhia {companhia}.")
            except requests.RequestException as e:
                print(f"Erro ao realizar a compra no servidor da companhia {companhia}: {e}")

def handle_client(con, adr, rotas):
    print(f"Cliente conectado: {adr}")
    con.send("Bem-vindo ao sistema de compra de passagens!\n".encode())
    con.send("Escolha seu número ID: ")
    client_ID = con.recv(1024).decode().strip()
    while True:
        rota_escolhida = listar_rotas(con, rotas)
        caminho_escolhido, companhia = listar_todos_trechos(con, rota_escolhida, rotas)
        enviar_mensagem(con, "Verificando a disponibilidade dos trechos...")
        with lock:  # Bloquear para garantir consistência
            if verificar_disponibilidade(caminho_escolhido, companhia):
                solicitar_permissao(client_ID, OUTRAS_COMPANHIAS)
                realizar_compra(caminho_escolhido, companhia)
                enviar_mensagem(con, "Compra realizada com sucesso! Todos os trechos foram adquiridos.")
            else:
                enviar_mensagem(con, "Não foi possível realizar a compra. Um ou mais trechos não possuem passagens suficientes.")
        enviar_mensagem("Escolha se deseja fazer mais alguma coisa: 'Sim para ficar'")
        resposta = con.recv(1024).decode().strip().lower()
        if resposta != "Sim":
            break
    con.close()
    print(f"Cliente desconectado: {adr}")

# Função principal do servidor
def main():
    # Obtém o nome da máquina local
    hostname = socket.gethostname()
    # Obtém o endereço IP associado ao nome da máquina
    ip_address = socket.gethostbyname(hostname)
    host = ip_address  # Escuta em todas as interfaces
    port = 43342
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