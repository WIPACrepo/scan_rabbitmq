#!/bin/bash
FILE=$(realpath $0)
#DIR=$(dirname $FILE)
DIR=$(PWD)


RABBITMQ=$(docker run -d --rm --network=host --hostname my-rabbit --name rabbit deadtrickster/rabbitmq_prometheus:3.7)
echo "started rabbitmq: $RABBITMQ"
PROM=$(docker run -d --rm --network=host -v $DIR/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus)
#PROM=$(docker run -d --rm --network=host -v prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus)
echo "started prometheus: $PROM"

#read -p 'press enter to stop images'

#docker stop "$PROM"
#docker stop "$RABBITMQ"
