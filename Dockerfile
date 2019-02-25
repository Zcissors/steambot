FROM python:3-alpine

LABEL maintainer="Vee"
LABEL version="1.1-SNAPSHOT"
LABEL description="pinguu"

VOLUME ["/pinguu"]
COPY requirements.txt requirements.txt
RUN apk add bash
RUN mkdir -p /pinguu && \
    apk add bash zlib-dev py3-pip git gcc coreutils libc-dev && \
    python -m pip install -U pip && \
    python -m pip install virtualenv && \
    python -m venv .venv && \
    source .venv/bin/activate && ls /pinguu -Rahl && \
    python -m pip install -Ur requirements.txt

CMD bash steambot
