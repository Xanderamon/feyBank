# pull official base image
FROM python:3.9-slim-bullseye

# set work directory
WORKDIR /usr/src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install necessary packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-lock.txt app/
# install pipenv and project dependencies
RUN pip install -r app/requirements-lock.txt
COPY . app/
