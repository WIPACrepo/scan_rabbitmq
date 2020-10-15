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
    zoom = hp.query_disc(nside,hp.pix2vec(nside,min_pix),np.radians(10))
    zoom_llh = skymap[zoom]
    diff_pix = zoom[(zoom_llh < err) & (zoom_llh > 0)]
    th,ph = hp.pix2ang(nside,diff_pix)
    diff_th,diff_ph = th - pos_th, ph - pos_ph
    if any(diff_ph<-np.pi):
       diff_ph[diff_ph<-np.pi] = diff_ph[diff_ph<-np.pi] + np.radians(360) 
    if any(diff_ph>pos_ph):
       diff_ph[diff_ph>np.pi] = diff_ph[diff_ph>np.pi] - np.radians(360) 
    min_th = diff_th.min()
    max_ph = diff_ph.max()
    min_ph = diff_ph.min()
    max_th = diff_th.max()
    return np.degrees(min_ph),np.degrees(max_ph),np.degrees(min_th),np.degrees(max_th) 

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

def fixpixnumber(nside,map_array):
    o_pix = map_array['pix'].astype(int)
    th_o, phi_o = hp.pix2ang(nside,o_pix)
    dec_o = th_o - np.pi/2
    th_fixed = np.pi/2 - dec_o 
    pix_fixed = hp.ang2pix(nside,th_fixed,phi_o)
    return pix_fixed



parser = argparse.ArgumentParser(description = "Read i3 output of a scan and convert to fits format")
parser.add_argument('-i', '--input', nargs = '+',dest = 'input',help = 'path to input file with scan results')
parser.add_argument('-o', '--output', dest = 'output',help = 'Prefix for output fits files')
args = parser.parse_args()

for pf in args.input:

    print(pf)
    frame_packet = load_frames(pf)
    
    #Extract event header info from the first Physics frame
    for f in frame_packet:
 #       if f.Stop == icetray.I3Frame.Physics and "CNN_classification" in f:
        if f.Stop == icetray.I3Frame.Physics:
           event_id = f["I3EventHeader"].event_id
           run_id = f["I3EventHeader"].run_id
           start_time = f["I3EventHeader"].start_time
           cnn = f["CNN_classification"]
           gfu = f["AlertInfoGFU"]
           hese = f["AlertInfoHESE"]
           alert_pass = f["AlertPassed"].value
           break

    cnn_vals = [float("%0.2e"%x) for x in cnn.values()]
    
    alert_type = None
    signalness = None
    far = None
    nu_energy = None
    alert_type = alert_pass

    if  hese.keys():
        if alert_type == 'hese-gold' or alert_type == 'hese-bronze':
    #    if hese['signalness'] and not np.isnan(hese['signalness']):
           signalness = hese['signalness']
           far = hese['yearly_rate']
           nu_energy = hese['E_nu_peak']
    if gfu.keys():
        if alert_type == 'gfu-bronze' or alert_type == 'gfu-gold':
     #   if gfu['signalness'] and not np.isnan(gfu['signalness']):
           signalness = gfu['signalness']
           far = gfu['yearly_rate']
           nu_energy = gfu['E_nu_peak']
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
      
      #map_info['pix'] = fixpixnumber(nside,map_info)
      pix_index = [int(p) for p in map_info['pix']]
      skymap[pix_index] = map_info['llh']
    #Find bestfit pixel
    min_pix = int(map_info[map_info['llh'] == min(map_info['llh'])]['pix'])
    th,ph = hp.pix2ang(nside,min_pix)
    ra = np.degrees(ph)
    
    dec = np.degrees(np.pi/2 - th)
    skymap = 2*skymap
    skymap = skymap - skymap[min_pix] #Rescale such that min LLH is at zero
    uncertainty = abs(np.asarray(pos_uncertainty(skymap,min_pix,64.2,nside)))
#    uncertainty = np.asarray(pos_uncertainty(skymap,min_pix,64.2,nside))
    deposited_e = map_info[map_info['pix']==min_pix]['energy']

    print("RA,DEC","Uncertainty")
    print(ra,dec,uncertainty)
    #Write FITS Header
    if nu_energy and not np.isnan(nu_energy):
       nu_energy = round(nu_energy/1000) #TeV
       far = np.around(far,2)
       signalness = np.around(signalness,3)
    else:
       print("Warning: Nan/empty fields in header")
    header = [('RUNID',run_id),
	  ('EVENTID',event_id),
          ('SENDER','IceCube Collaboration'),
          ('START','%s'%str(start_time.date_time),'Event Start date and time UTC'),
          ('EventMJD',start_time.mod_julian_day_double),
    	('I3TYPE','%s'%alert_type,'Alert Type'),
    	('RA',np.round(ra,2),'Degree'),
    	('DEC',np.round(dec,2),'Degree'),
	('RA_ERR_PLUS',np.round(uncertainty[1],2),'90% containment error high'),
	('RA_ERR_MINUS',np.round(uncertainty[0],2),'90% containment error low'),
	('DEC_ERR_PLUS',np.round(uncertainty[3],2),'90% containment error high'),
	('DEC_ERR_MINUS',np.round(uncertainty[2],2),'90% containment error low'),
    	('ENERGY',nu_energy, 'Estimated Neutrino Energy (TeV)'),
            ('FAR',far,'False alarm rate (per year)'),
            ('SIGNAL',signalness,'Signalness'),
          ('CASCADE_SCR',cnn_vals[0],'CNN classifier score for cascade'),
          ('SKIMMING_SCR',cnn_vals[1],'CNN classifier score for skimming event'),
          ('START_SCR',cnn_vals[2],'CNN classifier score for starting track'),
          ('STOP_SCR',cnn_vals[3],'CNN classifier score for stopping track'),
          ('THRGOING_SCR',cnn_vals[4],'CNN classifier score for through-going track'),
         #('CNNclass','Cascade,Skimming,Starting_Track,Stopping_Track,Through_Going_Track'),
         #('CNNscore','%s'%cnn_vals,'For each CNNClass'),
    	('COMMENTS','50%(90%) uncertainty location => Change in 2LLH of 22.2(64.2)'),
	('NOTE','Please ignore pixels with infinite or NaN values. They are rare cases of the minimizer failing to converge') ]
     
      
    #Save file
    hp.write_map("%sRun%s_%s_nside%s.fits.gz"%(args.output,run_id,event_id,nside),
        #skymap,coord = 'C',column_names = ['2LLH'],extra_header = header,overwrite = True)
        skymap,coord = 'C',column_names = ['2LLH'],extra_header = header)
    
    #Save bestfit loc
    print(run_id,ra,dec,deposited_e,min_pix) 
    ofile = 'scans_summary.txt'
    w = open(ofile,'a')
    w.write("%s\t%s\t%0.2f\t%0.2f\t%0.2f\t%0.2f\t%0.2f\t%0.2f\t%0.2f\t %s\t%s\n"%(run_id,event_id,ra,dec,uncertainty[0],uncertainty[1],uncertainty[2],uncertainty[3],deposited_e[0],signalness,far))
    w.close()


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




