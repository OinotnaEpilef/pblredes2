from socket import *
import requests
COMPANHIA = 0
OUTRAS_COMPANHIAS = {
    "A": "http://172.16.112.1:5000",
    "B": "http://172.16.112.2:5000",
    "C": "http://172.16.112.3:5000"
}
def exibir_mensagem(con):
    """
    Função para receber e exibir mensagens do servidor.
    """
    msg = con.recv(1024).decode()
    print(msg)

def escolher_servidor():
    """
    Permite ao cliente escolher o servidor (companhia) ao qual quer se conectar.
    """
    print("Selecione o servidor (companhia) para iniciar:")
    print("1 - Companhia A")
    print("2 - Companhia B")
    print("3 - Companhia C")
    
    opcao = input("Digite o número da companhia: ")
    if opcao == "1":
        COMPANHIA = "172.16.112.1"
        return "172.16.112.1", 10000
    elif opcao == "2":
        COMPANHIA = "172.16.112.2"
        return "172.16.112.2", 10000
    elif opcao == "3":
        COMPANHIA = "172.16.112.3"
        return "172.16.112.3", 10000, COMPANHIA
    else:
        print("Opção inválida.")
        return escolher_servidor()

def solicitar_permissao(cliente_id, companhias):
    """
    Solicita permissão a todos os servidores para garantir que o cliente tenha acesso
    exclusivo para a compra.
    """
    for companhia in companhias:
        url = f"http://{companhia}.com/solicitar_acesso"
        response = requests.post(url, json={"cliente_id": cliente_id})
        print(response.json())

def main():
    """
    Função principal do cliente.
    """
    cliente_id = input("Digite seu ID: ")
    host, port, companhia_atual = escolher_servidor()

    OUTRAS_COMPANHIAS.pop(COMPANHIA, None)
    
    # Estabelecendo conexão com o servidor escolhido
    client = socket(AF_INET, SOCK_STREAM)
    client.connect((host, port))
    while True:
        message = client.recv(1024).decode()
        print(message)
        if "Escolha" in message:
            choice = input("Digite sua escolha: ")
            solicitar_permissao(cliente_id, OUTRAS_COMPANHIAS)
            client.send(choice.encode())

if __name__ == "__main__":
    main()
