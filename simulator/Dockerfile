FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY backend ./backend
COPY simulator ./simulator

RUN python -m pip install \
    --no-cache-dir \
    --upgrade pip \
    && python -m pip install \
    --no-cache-dir .

EXPOSE 8101
EXPOSE 8102