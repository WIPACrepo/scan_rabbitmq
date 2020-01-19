from __future__ import print_function
from contextlib import contextmanager
import pickle
import base64
import argparse
import tempfile
import shutil
import subprocess
import os
import time

import pika

from icecube import icetray,dataio,dataclasses
from I3Tray import I3Tray

from producer import get_parser, get_queue
from consumer import consumer

icetray.logging.set_level('WARN')


def process_frames(frames):
    start = time.time()
    tmpdir = tempfile.mkdtemp(dir=os.getcwd())
    out_frames = []
    try:
        infilename = os.path.join(tmpdir,'in.i3')
        outfilename = os.path.join(tmpdir,'out.i3')
        with dataio.I3File(infilename, 'w') as f:
            for fr in frames:
                f.push(fr)
        subprocess.check_call(['python','worker_file_helper.py',infilename,outfilename])
        for fr in dataio.I3File(outfilename):
            out_frames.append(fr)
    finally:
        shutil.rmtree(tmpdir)
    print('time: ',time.time()-start)
    return out_frames

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', default='localhost', help='rabbitmq host')
    parser.add_argument('--timeout', type=int, default=10, help='queue timeout')
    parser.add_argument('-i', '--in_queue', help='input queue')
    parser.add_argument('-o', '--out_queue', help='input queue')
    args = parser.parse_args()

    with get_queue(args.address, args.in_queue) as (in_conn, in_channel), get_queue(args.address, args.out_queue) as (out_conn, out_channel):
        def callback(ch, method, properties, body):
            data = pickle.loads(body)
            if data['type'] == 'data':
                fr_in = data['frames']
                print('received frame', fr_in[0]['I3EventHeader'].event_id,
                      fr_in[0]['I3EventHeader'].sub_event_stream)
                fr_out = process_frames(fr_in)
                data2 = pickle.dumps({
                    'type': 'data',
                    'frames': fr_out,
                })
            else:
                raise Exception('bad type')
            out_channel.basic_publish(exchange='',
                                      routing_key=args.out_queue,
                                      body=data2)
        consumer(in_conn, in_channel, args.in_queue, callback, timeout=args.timeout)

    print('done!')

if __name__ == '__main__':
    main()
