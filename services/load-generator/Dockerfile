FROM python:3.9-slim-bullseye

WORKDIR /usr/src/load-generator

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "load_generator.py"]
