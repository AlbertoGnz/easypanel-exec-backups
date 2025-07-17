# Usa a imagem oficial do Debian como base
FROM debian:latest

# Instala o Python 3, o gerenciador de pacotes pip e outras utilidades
# -y responde sim para todas as perguntas
# && apt-get clean remove os arquivos de pacotes baixados para manter a imagem menor
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dotenv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho padrão dentro do contêiner
WORKDIR /app
