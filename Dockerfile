FROM python:3.6-alpine3.7

COPY . /python
WORKDIR /python

RUN pip install .
