FROM python:3.12-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero solo el requirements.txt para aprovechar la caché de Docker
# Si no cambia el requirements, Docker no reinstala las dependencias en cada build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Creamos la carpeta de uploads temporales
RUN mkdir -p uploads_tmp

EXPOSE 5000

CMD ["python", "app.py"]