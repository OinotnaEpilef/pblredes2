from socket import *
import json

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
    con = socket(AF_INET, SOCK_STREAM)
    con.connect((host, port))
    print("Conectado ao servidor:", host)
    
    # Recebendo lista de rotas disponíveis
    exibir_mensagem(con)  # Saudação inicial
    exibir_mensagem(con)  # Lista de rotas

    rota_escolhida = input("Escolha uma rota (por número): ")
    con.send(rota_escolhida.encode())
    
    # Exibindo todos os trechos da rota escolhida com indicação de companhia
    exibir_mensagem(con)  # Caminhos disponíveis

    # O cliente escolhe o trecho específico
    caminho_idx = input("Escolha o caminho (por número): ")
    con.send(caminho_idx.encode())
    
    trecho_idx = input("Escolha o trecho (por número): ")
    con.send(trecho_idx.encode())
    
    # Recebe a resposta da tentativa de reserva
    exibir_mensagem(con)

    # Fechar a conexão ao final da interação
    con.close()

if __name__ == "__main__":
    main()
