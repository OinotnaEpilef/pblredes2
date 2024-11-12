import socket

# Obtém o nome da máquina local
hostname = socket.gethostname()
# Obtém o endereço IP associado ao nome da máquina
ip_address = socket.gethostbyname(hostname)
print(ip_address)