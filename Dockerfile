# Utiliza una imagen oficial de Python
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /code

# Instala dependencias del sistema
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia los archivos de dependencias
COPY requirements.txt ./

# Instala las dependencias de Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la app
COPY . .

# Expone el puerto de la app
EXPOSE 8000

# Comando por defecto (puede ser sobreescrito por docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 