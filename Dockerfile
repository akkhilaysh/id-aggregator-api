FROM python:3.9-slim

WORKDIR /app

COPY app.py /app/

# Install dependencies
RUN pip install fastapi uvicorn requests redis pika


EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app:app", "--host=0.0.0.0", "--port=8000"]
