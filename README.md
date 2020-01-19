# scan_rabbitmq
Rabbit-mq based queueing setup for icecube alerts on AWS

Adapted from Dave Schultz rabbitmq-icetray and Claudio Kopper's skymap_scanner

## Start RabbitMQ
Follow the instructions at the following link to install and start rabbit-mq
https://www.rabbitmq.com/#getstarted

## Install pika
pip install pika

Or
#TODO: Make a functional docker image 
#Start RabbitMQ using a docker container:
#
#```
#resources/rabbitmq.sh
#```
#
#This starts both RabbitMQ and Prometheus.
#
#For monitoring, you can get built-in stats via http://localhost:15672
#and Prometheus via http://localhost:9090.

MAKE SURE YOU HAVE AN ICETRAY ENVIRONMENT RUNNING.

## Run a producer

A producer takes an input alert and prepares frames for individual pixels to be scanned. The number of pixels depends on nside specified in the producer_new.py script.

Example event: hese_event_01.json

```
python producer_new.py inputfile(either json or i3) -q inqueue -b path-to-baselineGCDdirectory
```
Remember to change the baseline input argument to wherever the baseGCD files are stored

## Run some workers
The workers take the frames sent by the producers in the inqueue and distribute them to the consumers through the outqueue
```
python worker.py -i inqueue -o outqueue
```
## Run a consumer
The consumers receive the frames sent by the workers, perform scans and save the output i3 files for every pixel



Make sure $I3_DATA environment variable points a directory containing photon-tables
```
python consumer_new.py outputresults-path -q outqueue
```

## Combine results for pixels after all scans
python find_bestframe -i path-to-scan-results
