FROM python:3.12-slim

WORKDIR /app

# Instalar dependências de sistema para pyswisseph e bibliotecas numéricas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libswe-dev \
    libswe0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

ENV ASTRO_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.web.app:app", "--host", "127.0.0.1", "--port", "8000"]
