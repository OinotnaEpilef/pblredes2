from socket import *

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
        return "172.16.112.1", 10000
    elif opcao == "2":
        return "172.16.112.2", 10000
    elif opcao == "3":
        return "172.16.112.3", 10000
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
    print("Conectado ao servidor:", host)
    print(client.recv(1024).decode())  # Mensagem de boas-vindas

    # Listar rotas disponíveis
    rotas = client.recv(1024).decode()
    print(rotas)

    # Escolher uma rota
    rota_escolhida = input("Escolha uma rota pelo número: ")
    client.send(rota_escolhida.encode())

    # Receber trechos disponíveis
    trechos_disponiveis = client.recv(1024).decode()
    print(trechos_disponiveis)

    # Escolher um trecho
    trecho_escolhido = input("Escolha um trecho pelo número: ")
    client.send(trecho_escolhido.encode())

    # Receber resposta sobre a reserva
    resposta = client.recv(1024).decode()
    print(resposta)

    client.close()

if __name__ == "__main__":
    main()
