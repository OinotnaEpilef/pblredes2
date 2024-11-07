# Usando a imagem oficial do Python
FROM python:3.11-slim

# Definindo o diretório de trabalho
WORKDIR /app

# Instalando dependências necessárias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiando o código fonte para o container
COPY server.py /app/

# Expondo a porta onde o servidor Flask vai rodar
EXPOSE 5000

# Comando para rodar o servidor
CMD ["python", "server.py"]
