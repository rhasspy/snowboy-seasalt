FROM debian:buster-slim as build

ENV LANG C.UTF-8

# IFDEF PROXY
#! RUN echo 'Acquire::http { Proxy "http://${APT_PROXY_HOST}:${APT_PROXY_PORT}"; };' >> /etc/apt/apt.conf.d/01proxy
# ENDIF

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        python3 python3-pip python3-venv python3-setuptools python3-dev \
        build-essential

# Create virtual environment
RUN mkdir -p /app && \
    cd /app && \
    python3 -m venv .venv && \
    .venv/bin/pip3 install --upgrade pip &&  \
    .venv/bin/pip3 install --upgrade setuptools wheel

COPY requirements.txt /app/
RUN /app/.venv/bin/pip3 install -r /app/requirements.txt

# -----------------------------------------------------------------------------

FROM debian:buster-slim as run

ENV LANG C.UTF-8

# IFDEF PROXY
#! RUN echo 'Acquire::http { Proxy "http://${APT_PROXY_HOST}:${APT_PROXY_PORT}"; };' >> /etc/apt/apt.conf.d/01proxy
# ENDIF

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        python python-scipy libpython2.7 python3 ffmpeg

# IFDEF PROXY
#! RUN rm -f /etc/apt/apt.conf.d/01proxy
# ENDIF

COPY seasalt/ /app/seasalt/
COPY --from=build /app/.venv/ /app/.venv/
COPY web/ /app/web/

# IFDEF PROXY
#! ENV PIP_INDEX_URL=http://${PYPI_PROXY_HOST}:${PYPI_PROXY_PORT}/simple/
#! ENV PIP_TRUSTED_HOST=${PYPI_PROXY_HOST}
# ENDIF

# IFDEF PROXY
#! ENV PIP_INDEX_URL=''
#! ENV PIP_TRUSTED_HOST=''
# ENDIF

COPY run.sh /

WORKDIR /app

EXPOSE 8000

ENTRYPOINT ["/bin/bash", "/run.sh"]