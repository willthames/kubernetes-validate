FROM python:3.12-alpine3.19

COPY . /python
WORKDIR /python

RUN pip install .
