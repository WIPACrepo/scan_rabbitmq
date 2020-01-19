#!/usr/bin/env python

import sys
from optparse import OptionParser

parser = OptionParser()
usage = """%prog [options]"""
parser.set_usage(usage)
parser.add_option("-o", "--output", action="store", type="string",
    default="output.json", dest="OUTPUT", help="Output JSON file")

# get parsed args
(options,args) = parser.parse_args()

filenames = args

from I3Tray import *
from icecube import icetray
from icecube import dataio
from icecube import full_event_followup

tray = I3Tray()

tray.Add(dataio.I3Reader, FilenameList=filenames)

# # whitelist of keys to send (online processing)
# keys = [
# "QFilterMask",
# "I3SuperDST",
# "CalibratedWaveformRange",
# "UncleanedInIcePulsesTimeRange",
# "SplitUncleanedInIcePulses",
# "SplitUncleanedInIcePulsesTimeRange",
# "DSTTriggers",
# "I3EventHeader",
# "I3FilterMask",
# # "I3GeometryDiff",
# # "I3CalibrationDiff",
# # "I3DetectorStatusDiff"
# ]

# whitelist of keys to send (kind of arbitrary list for offline processing)
keys = [
"QFilterMask",
"FilterMask",
"I3SuperDST",
# "SplitInIcePulses",
"SplitInIcePulsesTimeRange",
"CalibratedWaveformRange",
"UncleanedInIcePulsesTimeRange",
"SplitUncleanedInIcePulses",
"SplitUncleanedInIcePulsesTimeRange",
"DSTTriggers",
"I3EventHeader",
"I3FilterMask",
"SaturationWindows",
# "I3GeometryDiff",
# "I3CalibrationDiff",
# "I3DetectorStatusDiff"
"GRLSnapshotId",
"GoodRunStartTime",
"GoodRunEndTime",
"BadDomsList",
"BadDomsListSLC",
"NBadStrings"
]

tray.Add(full_event_followup.I3FullEventFollowupWriter,
    Keys = keys,
    WriterCallback = \
        full_event_followup.followup_writer_callback_to_file(options.OUTPUT),
    Streams = [
        icetray.I3Frame.Geometry,
        icetray.I3Frame.Calibration,
        icetray.I3Frame.DetectorStatus,
        icetray.I3Frame.DAQ,
        icetray.I3Frame.Physics
    ],
    # this could be an alternative, for example:
    # Streams = [icetray.I3Frame.DAQ, icetray.I3Frame.Physics],
    If = lambda f: True) # do this for all the frames in this example

tray.Execute()

del tray
