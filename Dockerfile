FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN playwright install --with-deps chromium

COPY ./src /code/src