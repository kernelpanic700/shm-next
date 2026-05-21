FROM python:3.12-slim as builder

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install --no-cache-dir build && \
    pip install --no-cache-dir poetry

COPY pyproject.toml ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12-slim as runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./scripts /app/scripts

EXPOSE 8000

CMD ["uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]