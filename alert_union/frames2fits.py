import os
import argparse
from icecube import dataio,dataclasses,icetray
from icecube import gulliver, millipede
from icecube.icetray import I3Units
import sys
from I3Tray import *
import glob
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
import numpy as np
import healpy as hp
from astropy.table import Table


def load_frames(infile):
    frame_packet = []
    i3f = dataio.I3File(infile)
    while True:
       if not i3f.more():
	  return frame_packet
       frame = i3f.pop_frame()
       frame_packet.append(frame)

def extract_results(fpacket,nside):
    names = ['pix','llh']
    p_results = []

    for f in frame_packet:
      if "MillipedeStarting2ndPass_millipedellh" in f:
        if f["SCAN_HealpixNSide"].value == nside:
	   fr_info = np.empty(1,[(n,float) for n in names])
           fr_info['pix'] = f["SCAN_HealpixPixel"].value
	   fr_info['llh'] = f["MillipedeStarting2ndPass_millipedellh"].logl
	   p_results.append(fr_info)
    
    return np.concatenate(p_results)


parser = argparse.ArgumentParser(description = "Read i3 output of a scan and convert to fits format")
parser.add_argument('-i', '--input', dest = 'input',help = 'path to input file with scan results')
parser.add_argument('-o', '--output', dest = 'output',help = 'Prefix for output fits files')
args = parser.parse_args()


pf = args.input 
frame_packet = load_frames(pf)
#Find nside from the Physics frame
ns_array = []
for f in frame_packet:
    if f.Stop == icetray.I3Frame.Physics:
       nside = f["SCAN_HealpixNSide"].value
       event_id = f["I3EventHeader"].event_id
       ns_array.append(nside)
#Extract pixel by pixel info
Nsides = sorted(np.unique(ns_array))

skymap = None

for nside in Nsides:
  map_info = extract_results(frame_packet,nside)
  
  #Write skymap
  npix = hp.nside2npix(nside)
  if skymap is not None:
     skymap = hp.ud_grade(skymap,nside)
  else:
     skymap = np.zeros(npix)

  pix_index = [int(p) for p in map_info['pix']]
  skymap[pix_index] = map_info['llh']
  

#Find bestfit pixel
min_pix = int(map_info[map_info['llh'] == min(map_info['llh'])]['pix'])
th,ph = hp.pix2ang(nside,min_pix)
ra = np.degrees(ph)
dec = np.degrees(th - np.pi/2)

#Write FITS Header
header = [('EVENTID','%s'%event_id),('EventMJD','567891','Date/Time of Alert'),
	('I3TYPE','IceCube AstroTrack Bronze'),
	('RA','%0.2f'%ra,'Degrees,J2000'),('DEC','%0.2f'%dec),
	('ENERGY','x TeV', 'Deposited energy at best-fit location'),
        ('FAR',0.5,'False alarm rate per year'),
	('SIG','-1','Signalness description'),
	('DNN','0.2','Classifier score in DNN Realtime Selection'),
	('COMMENTS','Penguins Against Capitalism')]


#Save file
hp.write_map("%s_nside%s.fits.gz"%(args.output,nside),
  skymap,column_names = ['LLH'],extra_header = header,overwrite = True)

#Alternate Using Astropy tables

#t = Table(map_info)


#hdr = fits.Header()
#hdr['EventID']= '1234'
#hdr['EventMJD'] = '56789'
#hdr['EventType'] = 'Gold/Bronze etc'
#hdr['Comment'] = 'Other information'
#table_hdu = fits.table_to_hdu(t,header=hdr)
#exit()
#empty_primary = fits.PrimaryHDU(header=hdr)
#hdu_list = fits.HDUList([empty_primary,
#			table_hdu])
#hdu_list.writeto('Test_scan2.fits.gz')

print("Done")




