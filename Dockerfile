FROM python:3.12-alpine3.19

ARG VERSION

RUN apk install sed
COPY entrypoint.sh /entrypoint.sh

RUN pip install kubernetes-validate==$(VERSION)

ENTRYPOINT ["/entrypoint.sh"]
