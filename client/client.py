from socket import *

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
        return "172.16.103.1", 43342
    elif opcao == "2":
        return "172.16.103.2", 43342
    elif opcao == "3":
        return "172.16.103.3", 43342
    else:
        print("Opção inválida.")
        return escolher_servidor()

def main():
    """
    Função principal do cliente.
    """
    host, port = escolher_servidor()
    
    # Estabelecendo conexão com o servidor escolhido
    client = socket(AF_INET, SOCK_STREAM)
    client.connect((host, port))
    while True:
        message = client.recv(1024).decode()
        print(message)
        if "Escolha" in message:
            choice = input("Digite sua escolha: ")
            client.send(choice.encode())

if __name__ == "__main__":
    main()
