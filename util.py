import logging
import pickle
import time
import argparse
import threading
from functools import partial
import signal

import pika


class DataError(Exception):
    pass

class RawQueue(object):
    def __init__(self, address='localhost', queue='test'):
        self.address = address
        self.queue = queue

    def __enter__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.address))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=False)
        self.channel.basic_qos(prefetch_count=1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

class SourceQueue(RawQueue):
    def send(self, data):
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue,
                                   body=data)

class SinkQueue(RawQueue):
    def __init__(self, callback=None, timeout=120, *args, **kwargs):
        super(SinkQueue, self).__init__(*args, **kwargs)
        self.callback = callback
        self.timeout = timeout
        self.consumer_id = None
        self.running = True
        self.last_time = time.time()

    def start_recv(self, callback=None):
        """Blocking recv call"""
        if callback:
            self.callback = callback
        self.consumer_id = self.channel.basic_consume(queue=self.queue,
                                                      auto_ack=False,
                                                      on_message_callback=self.handle_cb)
        t = threading.Thread(target=self.kill)
        t.daemon = True
        t.start()
        signal.signal(signal.SIGINT, self.stop)
        self.channel.start_consuming()

    def stop(self, *args, **kwargs):
        self.running = False
        self.connection.add_callback_threadsafe(partial(self.channel.basic_cancel, self.consumer_id))

    def handle_cb(self, ch, method, properties, body):
        if not self.running:
            ch.basic_nack(method.delivery_tag)
            raise KeyboardInterrupt()
        self.last_time = time.time()
        try:
            self.callback(body)
        except DataError:
            # bad data in the queue, so ack it to get rid of it
            logging.warning('error with data', exc_info=True)
            ch.basic_ack(method.delivery_tag)
        except Exception:
            logging.warning('error in callback', exc_info=True)
            ch.basic_nack(method.delivery_tag)
        else:
            ch.basic_ack(method.delivery_tag)

    def kill(self):
        now = time.time()
        try:
            while now-self.last_time <= self.timeout:
                time.sleep(1)
                now = time.time()
        finally:
            print('idle timeout hit')
            self.stop()

class Source:
    def __init__(self, queue):
        if not isinstance(queue, SourceQueue):
            raise Exception('queue is not a SourceQueue')
        self.queue = queue

    def send(self, frames):
        data = pickle.dumps({
            'type': 'data',
            'frames': frames,
        })
        self.queue.send(data)
#        print('Sent frame',frames[0].Stop)
        print('Sent frame', frames[-1]['I3EventHeader'].event_id,
              frames[-1]['I3EventHeader'].sub_event_stream)

class Sink:
    def __init__(self, queue, callback):
        if not isinstance(queue, SinkQueue):
            raise Exception('queue is not a SinkQueue')
        self.queue = queue
        self.callback = callback
        self.queue.callback = self.handle_cb

    def handle_cb(self, data):
        try:
            data = pickle.loads(data)
            if data['type'] == 'data':
                frames = data['frames']
 #               print('Received frame',frames[0].Stop)
                print('received frames', frames[-1]['I3EventHeader'].event_id,
                      frames[-1]['I3EventHeader'].sub_event_stream)
            else:
                raise DataError('bad data type')
        except Exception as e:
            raise DataError(e.message)
        else:
            self.callback(frames)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', default='localhost', help='rabbitmq host')
    parser.add_argument('-q', '--queue', default='test', help='queue name')
    parser.add_argument('--timeout', type=int, default=30, help='queue timeout')
    return parser
