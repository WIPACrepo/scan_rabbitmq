import matplotlib as mpl
#mpl.use("Agg")
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
    print('Please provide input map file')
    quit(1)

#Read input maps and sort them by nside
NSides = []
maps = []
headers = []
runs = []
ifiles = args.input

for f in ifiles:
    skymap, header = hp.read_map(f,h=True)
    nside = hp.get_nside(skymap)
    header = dict(header)
    maps.append(skymap)
    headers.append(header)
    NSides.append(nside)
    b = os.path.basename(f)
    runs.append(b[b.find("Run"):b.find("_")])
#NSides,maps,headers = zip(*sorted(zip(NSides,maps,headers)))

#ns_max = max(NSides)
#ns_min = min(NSides)



for nside, skymap, header,run in zip(NSides,maps, headers,runs):
   print(run)
#Mask out bad pixels
   pxls = np.arange(skymap.size)
   nZeroPix = pxls[(skymap != 0)]
   pxTh, pxPh = hp.pix2ang(nside,pxls)
  # values = np.ma.masked_where((pxTh > pxTh[nZeroPix].max())
  #                                 | (pxTh < pxTh[nZeroPix].min())
  #                                 | (skymap == hp.UNSEEN)
  #                                 | (skymap == 1e20,skymap)
   values = np.ma.masked_where((skymap == hp.UNSEEN)
				|(skymap == 1e20),skymap)
   
   #Find pixel with minimum LLH and create map boundaries
   min_pix = np.ma.where(values == values.min())[0]
   if len(min_pix) > 1:
      min_pix = [int(np.median(min_pix))]
      values = values - values[min_pix]     #Renormalize map
      max_TS = values[min_pix]
   else:
      values = values - values[min_pix]     #Renormalize map
      max_TS = values[min_pix]

    
   th,ph =  hp.pix2ang(nside,min_pix)
   src_ra = ph[0]
   src_dec = np.pi/2 - th[0]    #healpix convention
#   src_dec = th[0] - np.pi/2
   rad = np.radians(args.rad)
   print("Best pix: %s,2*deltaLLH:%s"%(min_pix,max_TS))
   print("RA %s, Dec %s"%(np.degrees(src_ra),np.degrees(src_dec)))
   xmin, xmax = src_ra - rad, src_ra + rad
   ymin, ymax = src_dec - rad, src_dec + rad
   
   xmin, xmax = np.degrees(xmin),np.degrees(xmax)
   ymin, ymax = np.degrees(ymin),np.degrees(ymax)
   margins = (0.05,0.25,0.05,0.05)
   vmax = values.min()+2000
 
   tfig   = plt.figure(num=1)
   img = hp.cartview(values,fig=1,
                coord=['C'], notext=True,
               lonra=[xmin,xmax],
               latra=[ymin,ymax],
               xsize=1000,
               min=values.min(), max=vmax,
               margins=margins,
               return_projected_map=True)
   plt.close(tfig)
   #Plot map zoomed around the alert
   r = np.degrees(src_ra)
   d = np.degrees(src_dec)
   f,ax = plt.subplots(1,1,figsize=(12,8))
   pos = ax.imshow(img,extent = [xmin,xmax,ymin,ymax],vmin = values.min(),vmax=vmax
   ,cmap = 'magma')
   
   f.colorbar(pos,orientation = 'horizontal',shrink = 0.6, label = r'$2\Delta$LLH')
   ax.plot(np.degrees(src_ra),np.degrees(src_dec),ls=None,marker = 'X',markersize = 13,color = 'w')
   ax.set(xlabel = "RA $[^\circ]$",ylabel = "$\delta [^\circ]$",title = "Run %s"%header['RUNID'])
   
   ax.grid()
   contour_levels = (np.array([22.2, 64.2])+max_TS) # these are values determined from MC by Will on the TS (2*LLH)
   contour_labels = [r'50%', r'90%']
   contour_colors=['y', 'r']

   CS = ax.contour(img,levels = contour_levels,colors=contour_colors, extent = [xmax,xmin,ymin,ymax])
   p1 = CS.collections[1].get_paths()[0]
   v = p1.vertices
   x = v[:,0]
   y = v[:,1]
#   for r,d in zip(x,y):
#       print(r,d)
   #Flip RA axis to astro convention
   ax.set_xlim(xmax,xmin)
   #ax.clabel(CS, inline=False, fontsize=12, fmt=dict(zip(contour_levels, contour_labels))) 
 #  circle0 = Circle((r,d),radius=4,facecolor = 'None',edgecolor = "r")
  # ax.add_patch(circle0) 
   if args.output:
      f.savefig('%s%s_%s_Nside%s.png'%(args.output,run,header['EVENTID'],nside))
      plt.close(f)
   else:
      plt.show()
   
   if args.allsky:
      fig = plt.figure(num=3,figsize=(11, 6))
      hp.mollview(skymap, fig=3,
               xsize=1000,
               coord=['C'],
               rot=180,cbar=True,unit = r'$2\Delta$LLH',
               cmap = 'magma',
               title=r"%s"%run)
      hp.projscatter(th,src_ra,marker = 'X',color= 'w',s=30)
      #hp.projscatter(src_dec-np.pi/2,src_ra,marker = 'X',color= 'w',s=30)
      hp.projtext(th+0.08,src_ra-0.08,"%s"%header['EVENTID'],color= 'w')
      ax1 = fig.get_axes()[0]
     # ax1.annotate("  0$^\circ$", xy=(1.65, 0.625), size="large")
#      ax1.annotate("360$^\circ$", xy=(-1.9, 0.625), size="large")
      ax1.text(2.0,0., r"$0^\circ$", ha="left", va="center")
      ax1.text(-2.0,0., r"$360^\circ$", ha="right", va="center")
      ax1.text(1.9,0.45, r"$30^\circ$", ha="left", va="center")
      ax1.text(1.4,0.8, r"$60^\circ$", ha="left", va="center")
      ax1.text(1.9,-0.45, r"$-30^\circ$", ha="left", va="center")
      ax1.text(1.4,-0.8, r"$-60^\circ$", ha="left", va="center")
      #hp.graticule()
      fig.savefig("%s%s_%sMollweide_Nside%s.png"%(args.output,run,header['EVENTID'],nside))
#      plt.show() 
      plt.close(fig)
