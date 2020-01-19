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

from I3Tray import *
from icecube import icetray
from icecube import dataio
from icecube import full_event_followup

tray = I3Tray()

tray.Add(full_event_followup.I3FullEventFollowupReader,
    ReaderCallback = \
        full_event_followup.followup_reader_callback_from_file(filename))

tray.Add("I3Writer", Filename=options.OUTPUT)

tray.Execute()

del tray
