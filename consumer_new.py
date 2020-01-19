from __future__ import print_function
import argparse
from functools import partial
import sys
from icecube import icetray,dataio,dataclasses
from I3Tray import I3Tray

from util import SinkQueue, Sink, get_parser
sys.path.append('scan')
from scan_pixel_distributed import scan_pixel_distributed_client

def writer(outfile, frames):
    with dataio.I3File(outfile, 'a') as f:
        for fr in frames:
	    print(fr.Stop)
            f.push(fr)

def main():
    parser = get_parser()
    parser.add_argument('outpath', help='output directory for results')
    parser.add_argument('-b','--baseline', default = 'baseline',help='direcotry with baseline GCD files')
    args = parser.parse_args()
   
    
    pulsesName="UncleanedInIcePulses"    
#    pulsesName="SplitUncleanedInIcePulsesLatePulseCleaned"    
    with SinkQueue(address=args.address, queue=args.queue, timeout=args.timeout) as queue:
        s = Sink(queue, callback=partial(scan_pixel_distributed_client,pulsesName=pulsesName,
	output=args.outpath,baseline=args.baseline))
        queue.start_recv()
    print('done!')

if __name__ == '__main__':
    main()
