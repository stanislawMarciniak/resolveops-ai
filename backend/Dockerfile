FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY backend ./backend
COPY documents ./documents

RUN python -m pip install \
    --no-cache-dir \
    --upgrade pip \
    && python -m pip install \
    --no-cache-dir .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]