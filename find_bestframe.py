import os
import argparse
from icecube import dataio,dataclasses
from icecube.icetray import I3Units
import sys
sys.path.append('scan')
from consolidate_scan import FindBestRecoResultForPixel
from I3Tray import I3Tray
import glob

def writer(frames):
    with dataio.I3File(outfile, 'a') as f:
         f.push(frames)


parser = argparse.ArgumentParser(description = "Read i3 files for all pixels for a scan and find best fit frames")
parser.add_argument('-i', '--input', dest = 'input',help = 'path to input directory with scan results')
parser.add_argument('--delete',action='store_true',help = 'delete individual i3 files after finding best fit')
args = parser.parse_args()

outd = args.input
outfile = '%s/BestFit_Frames.i3'%outd

files = sorted(glob.glob('%s/pix*i3'%args.input))
print("Finding best fit frames for %s pixels" %(len(files)))

for pf in files: 
   infile = dataio.I3File(pf)

   npos = 7  #No of position variations per pixel
   pos_vars = []
   
   for frame in infile:
       pos_vars.append(frame["SCAN_PositionVariationIndex"].value)
   
   print(sorted(pos_vars))
   
   if len(pos_vars)==npos:
      print("All position variations scanned for pixel %s" %(frame["SCAN_HealpixPixel"].value))
   
   #Determine best-fit
      tray = I3Tray()
      tray.Add(dataio.I3Reader,Filename=pf)
      tray.Add(FindBestRecoResultForPixel, "FindBestRecoResultForPixel",NPosVar = npos)
      tray.Add(writer,"writer")
      tray.Execute()
      tray.Finish()
      del tray
      if args.delete:
         print("Deleting Individual Pixel files to free up space")
         for df in files:
           os.system("rm %s"%df)

print("Done")




