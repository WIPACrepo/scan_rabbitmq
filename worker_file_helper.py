import sys
from icecube import icetray,dataio,dataclasses
from I3Tray import I3Tray

if len(sys.argv) < 3:
    raise Exception('must supply at least two filenames as arguments')

icetray.logging.set_level('WARN')
tray = I3Tray()
tray.Add('I3Reader', filenamelist=sys.argv[1:-1])
def test(fr):
    fr['NewKey'] = dataclasses.I3String('worker key')
tray.Add(test)
tray.Add('I3Writer',
         streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics],
         filename=sys.argv[-1],
        )
tray.Execute()