# Dockerfile para o servidor de venda de passagens
FROM python:3.11

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do servidor para o diretório de trabalho no container
COPY servidor.py /app/servidor.py

# Instala as dependências necessárias
RUN pip install requests

# Expõe a porta do servidor
EXPOSE 10000

# Comando para iniciar o servidor
CMD ["python", "servidor.py"]
