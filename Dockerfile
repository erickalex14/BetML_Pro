# BetML Pro — imagen única para API y scheduler (el comando decide cuál
# de los dos corre, ver docker-compose.prod.yml). Misma imagen para los
# dos servicios: comparten TODO el código (backend/) y las dependencias,
# tener dos Dockerfiles sería mantener lo mismo por duplicado.
FROM python:3.11-slim

# Playwright/Chromium necesita estas libs del sistema; sin ellas el
# scraping de Sofascore falla en runtime, no al construir la imagen.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates fonts-liberation libnss3 libnspr4 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# El índice extra es por torch: requirements pide "2.13.0+cpu", y ese
# sufijo solo existe en el repo de PyTorch, no en PyPI (sin esto el
# build muere con "No matching distribution found for torch==2.13.0+cpu").
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Chromium para Playwright — después de las libs de arriba
RUN python -m playwright install chromium

COPY backend/ ./backend/
# Modelos entrenados: sin esto la API arranca pero no puede predecir
COPY data/models/ ./data/models/

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
