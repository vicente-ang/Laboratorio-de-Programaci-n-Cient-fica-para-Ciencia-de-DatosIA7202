# Imagen del servicio de potabilidad: la API (FastAPI, puerto 8000) y la
# interfaz (Streamlit, puerto 8501) en un mismo contenedor.

# Imagen base con versión explícita: reconstruir mañana trae el mismo Python.
FROM python:3.13-slim

# `uv` desde su imagen oficial, también con versión fija.
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv

# Sin caché de uv en la capa y con el entorno virtual del proyecto en el PATH.
ENV UV_NO_CACHE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero lo que cambia poco: las dependencias. Esta capa se reutiliza
# mientras pyproject.toml y uv.lock no cambien.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --only-group servicio --no-install-project

# Un usuario sin privilegios: el servicio no corre como root. Se crea antes de
# copiar el código para que editar `src` no repita este paso.
RUN useradd --system --create-home --shell /usr/sbin/nologin aguaapr

# Después lo que cambia seguido: el código. En la etapa 4 el modelo viaja
# dentro de la imagen, porque en la nube no hay una carpeta que montar.
COPY src ./src
COPY models ./models

USER aguaapr

EXPOSE 8000 8501

# Docker consulta la ruta de vida de la API; se usa Python porque la imagen
# slim no trae curl.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

# Los dos procesos en segundo plano; `wait -n` termina el contenedor si
# cualquiera de los dos se detiene.
CMD ["bash", "-c", "uvicorn src.aguaapr.main:app --host 0.0.0.0 --port 8000 & streamlit run src/aguaapr/ui.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false & wait -n"]
