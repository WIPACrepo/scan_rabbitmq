#!/usr/bin/env python

# NOTE: this will only work if you have the "filterscripts" project
# in your meta-project - it does not come with vanilla icerec.
# -
# Use this to convert and base-process PFRaw files to something usable.

import sys
from optparse import OptionParser

parser = OptionParser()
usage = """%prog [options]"""
parser.set_usage(usage)
parser.add_option("-o", "--output", action="store", type="string",
    default="output.i3", dest="OUTPUT", help="Output i3 file")
parser.add_option("-d", "--no-decode", action="store_false", 
    dest="DECODE", default=True, help="Add the decoder to the processing")
parser.add_option("--no-qify", action="store_false", default=True,
    dest="QIFY", help="Apply QConverter, use if file is P frame only")

# get parsed args
(options,args) = parser.parse_args()

filenames = args

print "reading", filenames

from I3Tray import *

from icecube import icetray
from icecube import dataclasses
from icecube import dataio

from icecube import payload_parsing
from icecube.filterscripts.baseproc_onlinecalibration import OnlineCalibration
from icecube.filterscripts.baseproc_onlinecalibration import DOMCleaning
from icecube.filterscripts.baseproc_superdst import SuperDST, MaskMaker
from icecube.filterscripts import filter_globals

# TODO: once we have a new release of trigger-splitter, this should be changed:
icetray.load("trigger-splitter", False)
# TODO: to this:
# from icecube import trigger_splitter

tray = I3Tray()

tray.Add(dataio.I3Reader, FilenameList=filenames)

if options.QIFY:
    tray.Add("QConverter", WritePFrame=False)

if options.DECODE:
    tray.Add(payload_parsing.I3DOMLaunchExtractor,
                  'launches',
                  MinBiasID = 'MinBias',
                  FlasherDataID = 'Flasher',
                  CPUDataID = "BeaconHits",
                  )

tray.Add(DOMCleaning, 'DOMCleaning')

tray.Add(OnlineCalibration, 'Calibration',
                simulation = False)
            
tray.Add(SuperDST, 'SuperDST',
                InIcePulses=filter_globals.UncleanedInIcePulses,
                IceTopPulses='IceTopPulses',
                Output = filter_globals.DSTPulses
                )

tray.Add(MaskMaker, 'superdst_aliases',
               Output = filter_globals.DSTPulses,
               Streams=[icetray.I3Frame.DAQ]
               )

# call the trigger something else for the Q frame
def rename(frame, old, new):
    frame[new] = frame[old]
    del frame[old]
tray.Add(rename,
    old=filter_globals.triggerhierarchy,
    new=filter_globals.qtriggerhierarchy,
    Streams=[icetray.I3Frame.DAQ])

tray.Add('I3TriggerSplitter',filter_globals.InIceSplitter,
    TrigHierName=filter_globals.qtriggerhierarchy,
    # Note: taking the SuperDST pulses
    InputResponses=[filter_globals.InIceDSTPulses],
    OutputResponses=[filter_globals.SplitUncleanedInIcePulses],
    WriteTimeWindow = True)

tray.Add("I3Writer", Filename=options.OUTPUT,
    Streams=[icetray.I3Frame.Geometry, icetray.I3Frame.Calibration,
             icetray.I3Frame.DetectorStatus, icetray.I3Frame.DAQ,
             icetray.I3Frame.Physics])
         
tray.Execute()

del tray
