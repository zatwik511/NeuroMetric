FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential gcc libpq-dev --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a wsgi entrypoint and run as non-root
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

# Use gunicorn with the wsgi module
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "wsgi:app"]
