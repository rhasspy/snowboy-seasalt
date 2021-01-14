#!/usr/bin/env bash
if [ -n "${DOCKER_REGISTRY}" ]; then
    TAG_PREFIX="${DOCKER_REGISTRY}/"
fi

docker run -it \
       -p 8000:8000 \
       "${TAG_PREFIX}rhasspy/snowboy-seasalt" \
       "$@"
