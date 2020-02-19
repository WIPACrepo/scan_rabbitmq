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


def pos_uncertainty(skymap,min_pix,err,nside):
    pos_th,pos_ph = hp.pix2ang(nside,min_pix)
    zoom = hp.query_disc(nside,hp.pix2vec(nside,min_pix),np.radians(20))
    zoom_llh = skymap[zoom]
    diff_pix = zoom[(zoom_llh < err) & (zoom_llh >err-10)]
    th,ph = hp.pix2ang(nside,diff_pix)
    diff_th,diff_ph = abs(th - pos_th), abs(ph - pos_ph) 
    min_th = diff_th.min()
    max_ph = diff_ph.max()
    min_ph = diff_ph.min()
    max_th = diff_th.max()
    avg_ph = np.average([min_ph,max_ph])
    avg_th = np.average([min_th,max_th])
    return np.degrees(avg_ph),np.degrees(avg_th) 

def load_frames(infile):
    frame_packet = []
    i3f = dataio.I3File(infile)
    while True:
       if not i3f.more():
	  return frame_packet
       frame = i3f.pop_frame()
       frame_packet.append(frame)

def extract_results(fpacket,nside):
    names = ['pix','llh','energy']
    p_results = []

    for f in frame_packet:
      if "MillipedeStarting2ndPass_millipedellh" in f:
        if f["SCAN_HealpixNSide"].value == nside:
	   fr_info = np.empty(1,[(n,float) for n in names])
           fr_info['pix'] = f["SCAN_HealpixPixel"].value
	   fr_info['llh'] = f["MillipedeStarting2ndPass_millipedellh"].logl
	   fr_info['energy'] = f["MillipedeStarting2ndPass_totalRecoLossesTotal"].value
	   
	   p_results.append(fr_info)
    
    return np.concatenate(p_results)


parser = argparse.ArgumentParser(description = "Read i3 output of a scan and convert to fits format")
parser.add_argument('-i', '--input', nargs = '+',dest = 'input',help = 'path to input file with scan results')
parser.add_argument('-o', '--output', dest = 'output',help = 'Prefix for output fits files')
args = parser.parse_args()

for pf in args.input:
#pf = args.input
    frame_packet = load_frames(pf)
    
    #Extract event header info from the first Physics frame
    for f in frame_packet:
        if f.Stop == icetray.I3Frame.Physics and "CNN_classification" in f:
           event_id = f["I3EventHeader"].event_id
           run_id = f["I3EventHeader"].run_id
           start_time = f["I3EventHeader"].start_time
           cnn = f["CNN_classification"]
           gfu = f["AlertInfoGFU"]
           hese = f["AlertInfoHESE"]
           alert_pass = f["AlertPassed"].value
           break
    
    cnn_vals = [float("%0.2e"%x) for x in cnn.values()]
    if  hese.keys():
        if hese['pass_loose'] == 1 or hese['pass_tight'] == 1:
           signalness = hese['signalness']
           far = hese['yearly_rate']
           alert_type = 'HESE'
           nu_energy = hese['E_nu_peak']
    if gfu.keys():
        if gfu['pass_loose'] == 1 or gfu['pass_tight'] == 1 or gfu['pass_test'] == 1:
           signalness = gfu['signalness']
           far = gfu['yearly_rate']
	   alert_type = 'GFU'
           nu_energy = gfu['E_nu_peak']
    
    if alert_pass != 'none':
       alert_type = alert_pass
    print(alert_type)
    #Find nside from the Physics frame
    ns_array = []
    for f in frame_packet:
        if f.Stop == icetray.I3Frame.Physics:
           nside = f["SCAN_HealpixNSide"].value
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
         skymap = np.ones(npix)*np.inf
    
      pix_index = [int(p) for p in map_info['pix']]
      skymap[pix_index] = map_info['llh']
      
    #Find bestfit pixel
    min_pix = int(map_info[map_info['llh'] == min(map_info['llh'])]['pix'])
    th,ph = hp.pix2ang(nside,min_pix)
    ra = np.degrees(ph)
    dec = np.degrees(th - np.pi/2)
    skymap = 2*skymap
    skymap = skymap - skymap[min_pix] #Rescale such that min LLH is at zero
    uncertainty = pos_uncertainty(skymap,min_pix,64.2,nside)
     
    deposited_e = map_info[map_info['pix']==min_pix]['energy']
    
    #Write FITS Header
    if not np.isnan(nu_energy):
       nu_energy = int(nu_energy)
       far = np.around(far,2)
       signalness = np.around(signalness,3)
    else:
       print("Warning: Nan values in header")
    header = [('RUNID','%s'%run_id),
	  ('EVENTID','%s'%event_id),
          ('SENDER','IceCube Collaboration'),
          ('START','%s'%str(start_time.date_time),'Event Start date and time UTC'),
          ('EventMJD','%s'%start_time.mod_julian_day_double),
    	('I3TYPE','%s'%alert_type,'Alert Type'),
    	('RA','%0.2f +/- %.2f'%(ra,uncertainty[0]),'Degree. Error is 90% containment'),
	('DEC','%0.2f +/- %0.2f'%(dec,uncertainty[1]),'Degree. Error is 90% containment'),
    	('ENERGY','%s'%nu_energy, 'Estimated Neutrino Energy (GeV)'),
            ('FAR','%s'%far,'False alarm rate (per year)'),
            ('SIGNAL','%s'%signalness,'Signalness'),
          ('CNNclass','Cascade,Skimming,Starting_Track,Stopping_Track,Through_Going_Track'),
          ('CNNscore','%s'%cnn_vals,'For each CNNClass'),
    	('COMMENTS','50%(90%) unceratinty location => Change in 2LLH of 22.2(64.2)')]
     
      
    #Save file
    hp.write_map("%sRun%s_nside%s.fits.gz"%(args.output,run_id,nside),
        skymap,coord = 'C',column_names = ['2LLH'],extra_header = header,overwrite = True)
    
    #Save bestfit loc
    print(run_id,ra,dec,deposited_e,min_pix) 
    #ofile = 'alerts_out.txt'
    #w = open(ofile,'a')
    #w.write("%s\t%0.2f\t%0.2f\t%f,%s\n"%(run_id,ra,dec,deposited_e,min_pix))
    #w.close()


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




