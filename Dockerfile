# Copyright (c) 2018
# Cavium
#
# SPDX-License-Identifier: Apache-2.0
#
# Author: chencho <smunoz@cavium.com>


FROM alpine:3.7 AS builder

# add user and group first so their IDs don't change
RUN addgroup mosquitto && adduser -G mosquitto -D -H mosquitto

# su/sudo with proper signaling inside docker
RUN apk add --no-cache su-exec

ENV MOSQUITTO_VERSION="1.4.10-r2"
RUN set -xe \
	&& echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
	&& apk upgrade --update-cache --available \
    && apk add --no-cache --virtual mosquitto \
        mosquitto=${MOSQUITTO_VERSION} \
        mosquitto-libs=${MOSQUITTO_VERSION} \
        mosquitto-clients=${MOSQUITTO_VERSION} \
    \
    && apk add --no-cache --virtual python \
    && apk add --no-cache --virtual py-mongo \
    && apk add --no-cache --virtual py-requests \
    && mkdir -p /config /data/mosquitto /test \
    && chown -R mosquitto:mosquitto /data /config

COPY ./mosquitto_conf/* /config/
COPY ./test/* /test/
COPY ./launch.sh /

VOLUME ["/config", "/data", "/test"]
EXPOSE 1883 8883 9001
CMD ["sh", "-c", "/launch.sh $EDGEX_HOST $MQTT_HOST ${ROOMS}"]
