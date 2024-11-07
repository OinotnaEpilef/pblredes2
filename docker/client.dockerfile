# Dockerfile para o cliente de venda de passagens
FROM python:3.11

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do cliente para o diretório de trabalho no container
COPY cliente.py /app/cliente.py

# Instala as dependências necessárias
RUN pip install requests

# Comando para iniciar o cliente
CMD ["python", "cliente.py"]
