from __future__ import print_function
import argparse
import time

from icecube import icetray,dataio,dataclasses
from I3Tray import I3Tray

from util import SourceQueue, Source, SinkQueue, Sink, get_parser

icetray.logging.set_level('WARN')

class FrameReader(icetray.I3Module):
    def __init__(self, context):
        icetray.I3Module.__init__(self, context)
        self.AddParameter('frames', 'input frames', None)
        self.fr = None
    def Configure(self):
        frames = self.GetParameter('frames')
        if not isinstance(frames, list):
            raise Exception('"frames" should be a list')
        self.fr = frames
    def Process(self):
        if self.fr:
            self.PushFrame(self.fr.pop(0))
        else:
            self.RequestSuspension()

class FrameWriter(icetray.I3Module):
    def __init__(self, context, streams=None, output=[]):
        icetray.I3Module.__init__(self, context)
        self.AddParameter('frames', 'output frames', None)
        self.AddParameter('streams', 'accepted streams', None)
        self.streams = None
        self.fr = None
    def Configure(self):
        frames = self.GetParameter('frames')
        if not isinstance(frames, list):
            raise Exception('"frames" should be a list')
        self.fr = frames
        self.streams = self.GetParameter('streams')
    def Process(self):
        fr = self.PopFrame()
	self.fr.append(fr)
        #if self.streams and fr.Stop in self.streams:
        #    self.fr.append(fr)

def process_frames(frames):
    start = time.time()
    tray = I3Tray()
    tray.Add(FrameReader, frames=frames)
    def test(fr):
        fr['NewKey'] = dataclasses.I3String('worker key')
    tray.Add(test)
    out_frames = []
    tray.Add(FrameWriter,
             streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics],
             frames=out_frames,
            )
    tray.Execute()
    print('time: ',time.time()-start)
    return out_frames

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', default='localhost', help='rabbitmq host')
    parser.add_argument('--timeout', type=int, default=10, help='queue timeout')
    parser.add_argument('-i', '--in_queue', help='input queue')
    parser.add_argument('-o', '--out_queue', help='input queue')
    parser.add_argument('--sleep', default=0, type=int, help='sleep delay when processing work')
    args = parser.parse_args()

    with SinkQueue(address=args.address, queue=args.in_queue, timeout=args.timeout) as in_queue:
        with SourceQueue(args.address, args.out_queue) as out_queue:
            source = Source(out_queue)
            def cb(frames):
                frames2 = process_frames(frames)
                if args.sleep:
                    time.sleep(args.sleep)
                source.send(frames2)
            sink = Sink(in_queue, cb)
            in_queue.start_recv()

    print('done!')

if __name__ == '__main__':
    main()
