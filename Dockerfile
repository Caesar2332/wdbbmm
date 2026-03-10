FROM python:3.11-slim-bookworm

WORKDIR /app

COPY requirements_fastapi.txt .
RUN pip install --no-cache-dir -r requirements_fastapi.txt

COPY . .

RUN mkdir -p static

EXPOSE 8080

CMD ["python", "main.py"]
