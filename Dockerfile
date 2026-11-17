FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first for better build caching.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and database schema.
COPY pipeline/ ./pipeline/
COPY sql/ ./sql/
COPY tests/ ./tests/
COPY app.py ./app.py
# Default command for manual pipeline execution.
CMD ["python", "-m", "pipeline.flow"]
