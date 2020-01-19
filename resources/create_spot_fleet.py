#!/usr/bin/env python3
from __future__ import print_function
import sys
import os
import base64
import time
import math
import random
from datetime import datetime, timedelta
import contextlib
import argparse
import asyncio
from textwrap import dedent

import boto3
import botocore
import requests


class Specs(dict):
    """Default ec2 instance specs"""
    def __init__(self):
        super(Specs, self).__init__()
        self['ami'] = 'ami-03e5b5ce08fc21205'
        self['instance_types'] = {
            't3a.small': '0.008',
            't3.small': '0.008',
            't2.small': '0.008',
        }
        self['hours'] = 0.5
        self['keypair'] = 'dschultz'
        self['region'] = 'us-east-2'
        self['public_zones'] = {
        #    'us-east-2a': 'subnet-02f5744b98f61dda8',
        #    'us-east-2b': 'subnet-0204a7cc1b68e899b',
            'us-east-2c': 'subnet-059f890fb7b5618c0',
        }
        self['private_zones'] = {
        #    'us-east-2a': 'subnet-02f5744b98f61dda8',
        #    'us-east-2b': 'subnet-0204a7cc1b68e899b',
            'us-east-2c': 'subnet-059f890fb7b5618c0',
        }
        self['security_group'] = 'sg-1affe374'
        self['fleet_role'] = 'arn:aws:iam::085443031105:role/aws-service-role/spotfleet.amazonaws.com/AWSServiceRoleForEC2SpotFleet'


def format_user_data(text):
    text = dedent(text)
    if sys.version_info[0] < 3:
        return base64.b64encode(text)
    else:
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')


class Instance:
    """Wrapper for ec2 instance"""
    def __init__(self, ec2, user_data, spec, public=False, name='server'):
        self.ec2 = ec2
        self.user_data = user_data
        self.spec = spec
        self.public = public
        self.name = name

        self.request_id = None
        self.instance_id = None
        self.zone = None
        self.dnsname = None
        self.ipv6_address = None

    async def __aenter__(self):
        """
        Create and wait to come up.
        """
        user_data_b64 = format_user_data(self.user_data)
        if self.public:
            zones = self.spec['public_zones']
        else:
            zones = self.spec['private_zones']
        self.zone = random.choice(list(zones.keys()))

        ret = self.ec2.request_spot_instances(
            DryRun=False,
            SpotPrice=self.spec['price'],
            InstanceCount=1,
            Type='one-time',
            InstanceInterruptionBehavior='terminate',
            BlockDurationMinutes=int(math.ceil(self.spec['hours'])*60),
            LaunchSpecification={
                'ImageId': self.spec['ami'],
                'KeyName': self.spec['keypair'],
                'Placement': {
                    'AvailabilityZone': self.zone
                },
                'NetworkInterfaces': [
                    {
                        'AssociatePublicIpAddress': self.public, # for ipv4
                        'DeleteOnTermination': True,
                        'DeviceIndex': 0,
                        'Groups': [self.spec['security_group']],
                        'Ipv6AddressCount': 1,
                        'SubnetId': zones[self.zone],
                    }
                ],
                'UserData': user_data_b64,
                'InstanceType': self.spec['instance_type'],
            }
        )
        self.request_id = ret['SpotInstanceRequests'][0]['SpotInstanceRequestId']
        try:
            self.instance_id = ret['SpotInstanceRequests'][0]['InstanceId']
        except Exception:
            self.instance_id = None
        await asyncio.sleep(1)

        try:
            while not self.instance_id:
                print(self.name, 'waiting for server creation')
                ret = self.ec2.describe_spot_instance_requests(
                    SpotInstanceRequestIds=[self.request_id],
                )
                try:
                    self.instance_id = ret['SpotInstanceRequests'][0]['InstanceId']
                except Exception:
                    self.instance_id = None
                if not self.instance_id:
                    if 'Status' in ret['SpotInstanceRequests'][0] and 'Message' in ret['SpotInstanceRequests'][0]['Status']:
                        print(self.name, '  ', ret['SpotInstanceRequests'][0]['Status']['Message'])
                    await asyncio.sleep(10)

            while not self.ipv6_address:
                print(self.name, 'waiting for server startup')
                ret = self.ec2.describe_instances(
                    InstanceIds=[self.instance_id],
                )
                try:
                    self.dnsname = ret['Reservations'][0]['Instances'][0]['PublicDnsName']
                    for interface in ret['Reservations'][0]['Instances'][0]['NetworkInterfaces']:
                        self.ipv6_address = interface['Ipv6Addresses'][0]['Ipv6Address']
                        if self.ipv6_address:
                            break
                except Exception:
                    self.dnsname = None
                    self.ipv6_address = None
                if not self.ipv6_address:
                    await asyncio.sleep(5)
        except (KeyboardInterrupt,Exception):
            if self.request_id:
                self.ec2.cancel_spot_instance_requests(
                    SpotInstanceRequestIds=[self.request_id],
                )
            if self.instance_id:
                self.ec2.terminate_instances(
                    InstanceIds=[self.instance_id],
                )
            raise

        print(self.name, 'started', self.dnsname, self.ipv6_address)

    async def monitor(self, timeout=10000000000000000):
        """Monitor instance and die after `timeout` seconds."""
        end_time = time.time()+timeout
        while self.instance_id and time.time() < end_time:
            ret = self.ec2.describe_instances(
                InstanceIds=[self.instance_id],
            )
            try:
                assert ret['Reservations'][0]['Instances'][0]['State']['Name'] == 'running'
            except Exception:
                self.instance_id = None
            else:
                await asyncio.sleep(60)
        raise Exception(f'{self.name} instance terminated unexpectedly')

    async def __aexit__(self, exc_type, exc, tb):
        if self.request_id:
            self.ec2.cancel_spot_instance_requests(
                SpotInstanceRequestIds=[self.request_id],
            )
        if self.instance_id:
            self.ec2.terminate_instances(
                InstanceIds=[self.instance_id],
            )
            print(self.name, 'instance terminated')
        

class SpotFleet:
    """Wrapper for ec2 spot fleet"""
    def __init__(self, ec2, user_data, spec, num=1):
        self.ec2 = ec2
        self.user_data = user_data
        self.spec = spec
        self.num = num

        self.fleet_id = None

    async def __aenter__(self):
        """
        Create and wait to come up.
        """
        user_data_b64 = format_user_data(self.user_data)

        date_from = datetime.utcnow()
        date_to = date_from + timedelta(hours=self.spec['hours'])

        launch_specs = []
        for inst in self.spec['instance_types']:
            for zone in self.spec['private_zones']:
                launch_specs.append({
                    'ImageId': self.spec['ami'],
                    'KeyName': self.spec['keypair'],
                    'Placement': {
                        'AvailabilityZone': zone
                    },
                    'SecurityGroups': [
                        {
                            'GroupId': self.spec['security_group']
                        }
                    ],
                    'UserData': user_data_b64,
                    'InstanceType': inst,
                    'SpotPrice': self.spec['instance_types'][inst],
                    'SubnetId': self.spec['private_zones'][zone],
                })

        request = self.ec2.request_spot_fleet(
            SpotFleetRequestConfig={
                #'ClientToken': client_token,
                #'SpotPrice': self.spec['price'],
                'TargetCapacity': self.num,
                'ValidFrom': date_from.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'ValidUntil': date_to.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'TerminateInstancesWithExpiration': True,
                'IamFleetRole': self.spec['fleet_role'],
                'LaunchSpecifications': launch_specs,
                'Type': 'maintain',
                'AllocationStrategy': 'capacityOptimized',
            }
        )
        self.fleet_id = request['SpotFleetRequestId']
        print('fleet success:', self.fleet_id)

    
    async def monitor(self, timeout=10000000000000000):
        """Monitor instance and die after `timeout` seconds."""
        end_time = time.time()+timeout
        while self.instance_id and time.time() < end_time:
            ret = self.ec2.describe_instances(
                InstanceIds=[self.instance_id],
            )
            try:
                assert ret['Reservations'][0]['Instances'][0]['State']['Name'] == 'running'
            except Exception:
                self.instance_id = None
            else:
                await asyncio.sleep(60)
        raise Exception('fleet terminated')

    async def __aexit__(self, exc_type, exc, tb):
        if self.fleet_id:
            self.ec2.cancel_spot_fleet_requests(
                SpotFleetRequestIds=[self.fleet_id],
                TerminateInstances=True,
            )
            print('fleet terminated')


@contextlib.asynccontextmanager
async def setup_monitoring(address, target, token=None, service='ec2-test'):
    """Setup prometheus monitoring for target"""
    r = requests.put(os.path.join(address,service),
        json={'targets':[target+':9090']},
        headers={'Authorization':'bearer '+token},
    )
    r.raise_for_status()
    print('prometheus monitoring enabled')

    try:
        yield
    finally:
        r = requests.put(os.path.join(address,service),
            json={'targets':[]},
            headers={'Authorization':'bearer '+token},
        )
        r.raise_for_status()
        print('prometheus monitoring disabled')



async def main():
    parser = argparse.ArgumentParser(description='launch ec2 pool')
    parser.add_argument('--prometheus-reconfig', default='https://prometheus-reconfig-aws.icecube.wisc.edu',
                        help='Prometheus reconfig server')
    parser.add_argument('--prometheus-reconfig-token',
                        help='Prometheus reconfig token from token service')
    parser.add_argument('-n','--num', default=1, type=int,
                        help='number of servers in the worker pool')
    args = vars(parser.parse_args())


    spec = Specs()

    ec2 = boto3.client('ec2', region_name=spec['region'])

    token = open('token').read().strip()

    mem_spec = spec.copy()
    mem_spec['instance_type'] = 'm5a.large'
    mem_spec['price'] = '0.05'
    
    t3a_spec = spec.copy()
    t3a_spec['instance_type'] = 't3a.medium'
    t3a_spec['price'] = '0.03'

    cpu_spec = spec.copy()
    cpu_spec['instance_type'] = 'm5a.large'
    cpu_spec['price'] = '0.048'


    monitoring_user_data = """\
    #!/bin/bash
    cat >$PWD/prometheus.yml <<EOF
    global:
      scrape_interval: 15s # graphs disappear from grafana with default for some reason
    scrape_configs:
      - job_name: 'system'
        honor_labels: true
        file_sd_configs:
        - files:
           - /etc/prometheus/system_targets.json
          refresh_interval: 15s
      - job_name: 'rabbitmq'
        metrics_path: '/api/metrics'
        honor_labels: true
        file_sd_configs:
        - files:
           - /etc/prometheus/rabbitmq_targets.json
          refresh_interval: 15s
    EOF
    cat >$PWD/system_targets.json <<EOF
    [{
      "targets": ["localhost:9100"],
      "labels": {
        "service":"system",
        "component":"monitoring"
      }
    }]
    EOF
    chmod a+rw $PWD/system_targets.json
    echo "[]" >$PWD/rabbitmq_targets.json
    chmod a+rw $PWD/rabbitmq_targets.json
    cat >$PWD/prometheus_reconfig.json <<EOF
    {
      "services": [
        {"name": "system",
         "filename": "/system_targets.json"
        },
        {"name": "rabbitmq",
         "filename": "/rabbitmq_targets.json"
        }
      ]
    }
    EOF

    printf "\\n%s\\n"  "Running docker"
    docker pull wipac/prometheus-reconfig:latest
    docker run --rm -d -p 8080:8080 -v $PWD/prometheus_reconfig.json:/etc/prometheus_reconfig.json -v $PWD/system_targets.json:/system_targets.json -v $PWD/rabbitmq_targets.json:/rabbitmq_targets.json wipac/prometheus-reconfig:latest
    docker run --rm --network host -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml -v $PWD/system_targets.json:/etc/prometheus/system_targets.json -v $PWD/rabbitmq_targets.json:/etc/prometheus/rabbitmq_targets.json prom/prometheus
    printf "\\n%s\\n"  "Docker is complete, shutting down"
    shutdown -hP now
    """

    rabbitmq_user_data = """\
    #!/bin/bash
    server="{}"

    printf "%s" "waiting for Server ..."
    while ! timeout 0.2 ping -c 1 -n $server &> /dev/null
    do
        printf "%c" "."
    done
    printf "\\n%s\\n"  "Server is online"
    sleep 1

    ipv6=`ip -br -6 addr show scope global|grep UP|grep -v docker|awk '{{print $3}}'|awk -F'/' '{{print $1}}'`
    curl -XPATCH -d "{{\\"targets\\":[\\"[$ipv6]:9100\\"]}}" http://[$server]:8080/system/rabbitmq
    curl -XPATCH -d "{{\\"targets\\":[\\"[$ipv6]:15672\\"]}}" http://[$server]:8080/rabbitmq/rabbitmq

    printf "\\n%s\\n"  "Running docker"
    docker run --rm -p 5672:5672 -p 15672:15672 deadtrickster/rabbitmq_prometheus:3.7
    printf "\\n%s\\n"  "Docker is complete, shutting down"
    shutdown -hP now
    """

    producer_user_data = """\
    #!/bin/bash
    queue_server="{}"
    mon_server="{}"

    wget http://icecube:skua@convey.icecube.wisc.edu/data/exp/IceCube/2018/filtered/level2/0620/Run00131194_73/Level2_IC86.2018_data_Run00131194_Subrun00000000_00000000.i3.zst
    docker pull wipac/rabbitmq-icetray

    printf "%s" "waiting for Server ..."
    while ! timeout 0.2 ping -c 1 -n $mon_server &> /dev/null
    do
        printf "%c" "."
    done
    while ! timeout 0.2 ping -c 1 -n $queue_server &> /dev/null
    do
        printf "%c" "."
    done
    printf "\\n%s\\n"  "Server is online"
    sleep 1

    ipv6=`ip -br -6 addr show scope global|grep UP|grep -v docker|awk '{{print $3}}'|awk -F'/' '{{print $1}}'`
    curl -XPATCH -d "{{\\"targets\\":[\\"[$ipv6]:9100\\"]}}" http://[$mon_server]:8080/system/producer

    printf "\\n%s\\n"  "Running docker"
    docker run --network=host -v $PWD:/mnt --rm --entrypoint /bin/bash wipac/rabbitmq-icetray /usr/local/icetray/env-shell.sh python /local/producer.py -q inqueue -a $queue_server /mnt/Level2_IC86.2018_data_Run00131194_Subrun00000000_00000000.i3.zst
    printf "\\n%s\\n"  "Docker is complete, shutting down"
    shutdown -hP now
    """

    consumer_user_data = """\
    #!/bin/bash
    queue_server="{}"
    mon_server="{}"
    docker pull wipac/rabbitmq-icetray

    printf "%s" "waiting for Server ..."
    while ! timeout 0.2 ping -c 1 -n $mon_server &> /dev/null
    do
        printf "%c" "."
    done
    while ! timeout 0.2 ping -c 1 -n $queue_server &> /dev/null
    do
        printf "%c" "."
    done
    printf "\\n%s\\n"  "Server is online"
    sleep 1

    ipv6=`ip -br -6 addr show scope global|grep UP|grep -v docker|awk '{{print $3}}'|awk -F'/' '{{print $1}}'`
    curl -XPATCH -d "{{\\"targets\\":[\\"[$ipv6]:9100\\"]}}" http://[$mon_server]:8080/system/consumer

    printf "\\n%s\\n"  "Running docker"
    docker run --network=host -v $PWD:/mnt --rm --entrypoint /bin/bash wipac/rabbitmq-icetray /usr/local/icetray/env-shell.sh python /local/consumer.py -q outqueue --timeout 180 -a $queue_server /mnt/out.i3.zst
    printf "\\n%s\\n"  "Docker is complete, shutting down"
    shutdown -hP now
    """

    worker_user_data = """\
    #!/bin/bash
    queue_server="{}"
    mon_server="{}"
    docker pull wipac/rabbitmq-icetray

    printf "%s" "waiting for Server ..."
    while ! timeout 0.2 ping -c 1 -n $mon_server &> /dev/null
    do
        printf "%c" "."
    done
    while ! timeout 0.2 ping -c 1 -n $queue_server &> /dev/null
    do
        printf "%c" "."
    done
    printf "\\n%s\\n"  "Server is online"
    sleep 1

    ipv6=`ip -br -6 addr show scope global|grep UP|grep -v docker|awk '{{print $3}}'|awk -F'/' '{{print $1}}'`
    curl -XPATCH -d "{{\\"targets\\":[\\"[$ipv6]:9100\\"]}}" http://[$mon_server]:8080/system/worker

    printf "\\n%s\\n"  "Running docker"
    docker run --network=host --rm wipac/rabbitmq-icetray -a $queue_server -i inqueue -o outqueue --timeout 360 --sleep 60
    printf "\\n%s\\n"  "Docker is complete, shutting down"
    shutdown -hP now
    """

    futures = []
    async with contextlib.AsyncExitStack() as stack:
        mon_server = Instance(ec2, monitoring_user_data, mem_spec, public=True, name='monitoring')
        await stack.enter_async_context(mon_server)
        futures.append(mon_server.monitor(spec['hours']*3600))

        queue_server = Instance(ec2, rabbitmq_user_data.format(mon_server.ipv6_address), cpu_spec, name='rabbitmq')
        await stack.enter_async_context(queue_server)
        futures.append(queue_server.monitor(spec['hours']*3600))
        await stack.enter_async_context(setup_monitoring(
                args['prometheus_reconfig'], mon_server.dnsname, token=token))

        producer = Instance(ec2, producer_user_data.format(queue_server.ipv6_address, mon_server.ipv6_address), t3a_spec, public=True, name='producer')
        consumer = Instance(ec2, consumer_user_data.format(queue_server.ipv6_address, mon_server.ipv6_address), t3a_spec, name='consumer')
        fleet = SpotFleet(ec2, worker_user_data.format(queue_server.ipv6_address, mon_server.ipv6_address), spec, num=args['num'])
        await stack.enter_async_context(producer)
        #futures.append(producer.monitor(spec['hours']*3600))
        await stack.enter_async_context(consumer)
        futures.append(consumer.monitor(spec['hours']*3600))
        await stack.enter_async_context(fleet)

        await asyncio.wait(futures, return_when=asyncio.FIRST_EXCEPTION)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
