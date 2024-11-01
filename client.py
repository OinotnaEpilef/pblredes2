from socket import *
import json

def main():
    # Conectando ao servidor VENDEPASS de uma companhia específica
    print("Selecione o servidor para conexão:")
    print("1 - Companhia A")
    print("2 - Companhia B")
    print("3 - Companhia C")
    opcao = input("Escolha a opção: ")

    servidor = {
        "1": ("172.16.112.1", 10000),
        "2": ("172.16.112.2", 10000),
        "3": ("172.16.112.3", 10000)
    }[opcao]

    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect(servidor)

    while True:
        mensagem = client_socket.recv(1024).decode()
        print(mensagem)
        
        # Responder com JSON se necessário
        if "Escolha" in mensagem:
            resposta = input("Sua escolha: ")
            client_socket.send(resposta.encode())

if __name__ == "__main__":
    main()
