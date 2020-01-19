#!/usr/bin/env python

import sys
from optparse import OptionParser

parser = OptionParser()
usage = """%prog [options]"""
parser.set_usage(usage)
parser.add_option("-o", "--output", action="store", type="string",
    default="output.i3", dest="OUTPUT", help="Output i3 file")

# get parsed args
(options,args) = parser.parse_args()

if len(args) != 1:
    raise RuntimeError("please specify exactly one filename")

filename = args[0]

print "reading data from", filename
print "writing output to", options.OUTPUT

from I3Tray import *
from icecube import icetray
from icecube import dataio
from icecube import full_event_followup

tray = I3Tray()

icetray.logging.set_level_for_unit("followup_reader_callback", "INFO")

def followup_reader_callback(filename,
    frame_object_names=["HESEFollowupMessage",
    "HESEFollowupMessageLowPrio"]):
    
    i3f = dataio.I3File(filename)
    
    def func():
        while True:
            pframe = i3f.pop_physics()
            if pframe is None:
                i3f.close()
                return None

            found_object=None
            for frame_object_name in frame_object_names:
                if frame_object_name in pframe:
                    found_object=frame_object_name
                    break
            if found_object is not None:
                break
        
        icetray.logging.log_info(
            "found message type: \"{0}\"".format(found_object),
            "followup_reader_callback")
        msg = pframe[found_object].value

        packet = \
            full_event_followup.i3live_json_to_frame_packet(
                msg, pnf_framing=False)
        return packet
    return func

tray.Add(full_event_followup.I3FullEventFollowupReader,
    ReaderCallback = followup_reader_callback(filename))

tray.Add("I3Writer", Filename=options.OUTPUT)

tray.Execute()

del tray
