import matplotlib as mpl
mpl.rc('font',family='serif',size=18)
mpl.rc("text",usetex = True)
import matplotlib.pyplot as plt
import numpy as np
import healpy as hp
import argparse
from astropy.io import fits
from astropy.table import Table
import os
from matplotlib.patches import Circle

p = argparse.ArgumentParser(description='Plot skymap from an input fits file')
p.add_argument('input', nargs = "+",type=str, default=None,
               help='Input FITS file(s)')
p.add_argument('-o','--output',type=str,default=None,
		help='Output file name for saving plot')
p.add_argument('-r', '--rad', type=float, default=10.,
               help='Max radius of region to plot around the alert in degrees')

p.add_argument('-s','--allsky',type=str,default=None,
		help='Creat all-sky map in Mollweide projection')

args = p.parse_args()

if args.input is None:
    print 'Please provide input map file'
    quit(1)

#Read input maps and sort them by nside
NSides = []
maps = []
headers = []

ifiles = args.input

for f in ifiles:
    skymap, header = hp.read_map(f,h=True)
    nside = hp.get_nside(skymap)
    header = dict(header)
    maps.append(skymap)
    headers.append(header)
    NSides.append(nside)

NSides,maps,headers = zip(*sorted(zip(NSides,maps,headers)))

ns_max = max(NSides)
ns_min = min(NSides)



for nside, skymap, header in zip(NSides,maps, headers):
#Mask out bad pixels
   pxls = np.arange(skymap.size)
   nZeroPix = pxls[(skymap != 0)]
   pxTh, pxPh = hp.pix2ang(nside,pxls)
   values = np.ma.masked_where((pxTh > pxTh[nZeroPix].max())
                                   | (pxTh < pxTh[nZeroPix].min())
                                   | (skymap == hp.UNSEEN)
                                   | (skymap == 1e20)
                                   |(skymap==0) , skymap)
   
   #Find pixel with minimum LLH and create map boundaries
   min_pix = np.ma.where(values == values.min())
   values = values - values[min_pix]     #Renormalize map
   values = 2*values     #TS = 2*DeltaLLH
   max_TS = values[min_pix]  
    
   th,ph =  hp.pix2ang(nside,min_pix)
   src_ra = ph[0]
   src_dec = np.pi/2 - th[0]    #healpix convention
   #src_dec = th[0] - np.pi/2
   rad = np.radians(args.rad)
   
   xmin, xmax = src_ra - rad, src_ra + rad
   ymin, ymax = src_dec - rad, src_dec + rad
   
   xmin, xmax = np.degrees(xmin),np.degrees(xmax)
   ymin, ymax = np.degrees(ymin),np.degrees(ymax)
   
   margins = (0.05,0.25,0.05,0.05)
   
   tfig   = plt.figure(num=1)
   img = hp.cartview(values,fig=1,
                coord=['C'], notext=True,
               lonra=[xmin[0],xmax[0]],
               latra=[ymin[0],ymax[0]],
               xsize=1000,
               min=values.min(), max=values.max(),
               margins=margins,
               return_projected_map=True)
   plt.close(tfig)
   
   #Plot map zoomed around the alert
   r = np.degrees(src_ra)
   d = np.degrees(src_dec)
   print(r,d)
   f,ax = plt.subplots(1,1,figsize=(12,8))
   pos = ax.imshow(img,extent = [xmin[0],xmax[0],ymin[0],ymax[0]],vmin = values.min(),vmax=values.max()/2.5
   ,cmap = 'magma')
   
   f.colorbar(pos)
   ax.plot(np.degrees(src_ra),np.degrees(src_dec),ls=None,marker = 'X',markersize = 16,color = 'w')
   ax.set(xlabel = "RA $[^\circ]$",ylabel = "$\delta [^\circ]$",title = "NSIDE %s"%header['NSIDE'])
   
   ax.grid()
   contour_levels = (np.array([22.2, 64.2])+max_TS) # these are values determined from MC by Will on the TS (2*LLH)
   contour_labels = [r'50%', r'90%']
   contour_colors=['y', 'r']

#   CS = ax.contour(img,levels = contour_levels,colors=contour_colors, extent = [xmin[0],xmax[0],ymin[0],ymax[0]])
 #  ax.clabel(CS, inline=False, fontsize=12, fmt=dict(zip(contour_levels, contour_labels))) 
   circle0 = Circle((r,d),radius=4,facecolor = 'None',edgecolor = "r")
   ax.add_patch(circle0) 
   if args.output:
      f.savefig('%s_Nside%s.png'%(args.output,nside))
      plt.close(f)
   else:
      plt.show()
   
   if args.allsky:
      fig = plt.figure(num=3,figsize=(11, 6))
      hp.mollview(skymap, fig=3,
               xsize=1000,
               coord=['C'],
               rot=0,cbar=True,
               cmap = 'magma',
               title=r"NSIDE %s"%nside)
      hp.projscatter(th,src_ra,marker = 'X',color= 'w',s=30)
      #hp.projscatter(src_dec-np.pi/2,src_ra,marker = 'X',color= 'w',s=30)
      hp.projtext(th+0.08,src_ra-0.08,"IC200120",color= 'w')
      ax1 = fig.get_axes()[0]
      #hp.graticule()
      fig.savefig("%sMollweide_Nside%s.png"%(args.allsky,nside))
   #   plt.show() 
      plt.close(fig)
