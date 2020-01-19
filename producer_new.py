from __future__ import print_function
import argparse
import sys
from icecube import icetray,dataio,dataclasses
from I3Tray import I3Tray
import json
from util import SourceQueue, Source, get_parser

sys.path.append('inframe_maker')
sys.path.append('scan')
from frame_gen import extract_json_message
from send_scan import SendPixelsToScan

class SimpleSource(icetray.I3Module):
    '''
    Simple source module. It acquires frames from the event and pushes them to downstream modules.
    '''
    def __init__(self, context):
        icetray.I3Module.__init__(self, context)
        self.AddParameter('json', 'frame packet extracted from json file', None)
    def Configure(self):
	self.json = self.GetParameter('json')
    def Process(self):
        if self.json:
	   f = self.json.pop(0)
           self.PushFrame(f)
        else:
	   self.RequestSuspension()


class FramePacker(icetray.I3Module):
    def __init__(self, context):
        icetray.I3Module.__init__(self, context)
        self.AddParameter('sender', 'sender function', None)
        self.sender = None
        self.frames = []
        self.accept_frames = [icetray.I3Frame.DAQ, icetray.I3Frame.Physics]
    def Configure(self):
        self.sender = self.GetParameter('sender')
    def Process(self):
	fr = self.PopFrame()
        self.frames.append(fr)
	print(fr.Stop)
	if fr.Stop == icetray.I3Frame.Physics:
        #if self.frames:
                self.sender(self.frames)
                self.frames = []

def main():
    parser = get_parser()
    #parser.add_argument('infile', help='input i3 file')
    parser.add_argument('infile', help='input json or i3 file')
    args = parser.parse_args()
    
    json_blob_handle = args.infile

    if len(json_blob_handle) == 0:
        raise RuntimeError("need to specify at least one input filename")

    #Read and extract
    if '.i3' in json_blob_handle:
       inputi3 = dataio.I3File(json_blob_handle)
       fpacket = [f for f in inputi3]
    else:

       with open(json_blob_handle) as json_data:
               event = json.load(json_data)
       del json_blob_handle
       
       fpacket = extract_json_message(event)
    with SourceQueue(args.address, args.queue) as queue:
        s = Source(queue)
        tray = I3Tray()
	tray.AddModule(SendPixelsToScan, "SendPixelsToScan",
        FramePacket=fpacket,
        NSide=1,
        InputTimeName="HESE_VHESelfVetoVertexTime",
        InputPosName="HESE_VHESelfVetoVertexPos",
        OutputParticleName="MillipedeSeedParticle",
    )
        tray.Add(FramePacker, sender=s.send)
        tray.Execute()

    print('done!')

if __name__ == '__main__':
    main()
