FROM python:3.6-alpine

LABEL maintainer="Vee"
LABEL version="1.0-SNAPSHOT"
LABEL description="pinguu"

VOLUME ["/pinguu"]
COPY requirements.txt requirements.txt
RUN mkdir -p /pinguu && \
    apk add bash zlib-dev py3-pip git gcc coreutils libc-dev && \
    python3 -m pip install virtualenv && \
    python3 -m venv .venv && \
    source .venv/bin/activate && ls /pinguu -Rahl && \
    python3 -m pip install -r requirements.txt

CMD bash -c "source /.venv/bin/activate && cd /pinguu && python3 -m pinguu"
