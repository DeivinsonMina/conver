# Usa una imagen base ligera de Python
FROM python:3.11-slim

# Instala LibreOffice y otras dependencias necesarias
RUN apt-get update && apt-get install -y \
    libreoffice \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia primero los requerimientos y luego el resto del código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expone el puerto que usará Flask
EXPOSE 8080

# Comando para iniciar la app
CMD ["python", "app.py"]

