FROM python:3.10-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e .
COPY . /app
EXPOSE 8000
CMD ["uvicorn", "trust_before_touch.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
