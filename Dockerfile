FROM sanicframework/sanic:3.10-latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /var/www/html

RUN apk update \
    && apk add --no-cache python3-dev libpq-dev build-base bash

COPY ./src/requirements.txt /var/www/html
RUN pip3 install -r requirements.txt

ADD ./src /var/www/html
