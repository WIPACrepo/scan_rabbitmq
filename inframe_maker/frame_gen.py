
import os
import sys
import logging
import json
import argparse
from icecube import icetray, dataclasses, dataio
from icecube import full_event_followup, frame_object_diff

from utils import create_event_id, save_GCD_frame_packet_to_file, hash_frame_packet

def extract_json_message(json_data):

    # extract the packet
    frame_packet = full_event_followup.i3live_json_to_frame_packet(json.dumps(json_data), pnf_framing=True)

    r = __extract_frame_packet(frame_packet)
    event_id = r[0]
    state_dict = r[1]
    
    return state_dict
    #return event_id,state_dict
    
def __extract_frame_packet(frame_packet, pulsesName="SplitUncleanedInIcePulses"):
    if frame_packet[-1].Stop != icetray.I3Frame.Physics and frame_packet[-1].Stop != icetray.I3Frame.Stream('p'):
        raise RuntimeError("frame packet does not end with Physics frame")

    physics_frame = frame_packet[-1]

    # extract event ID
    header = physics_frame["I3EventHeader"]
    event_id_string = create_event_id(header.run_id, header.event_id)
    print("event ID is {0}".format(event_id_string))




    
    GCDQp_filename =  "%s_GCDQP.i3"%event_id_string 
    save_GCD_frame_packet_to_file(frame_packet, GCDQp_filename)
    print("wrote GCDQP dependency frames to {0}".format(GCDQp_filename))
    state_dict = frame_packet 

    return (event_id_string, state_dict)
    #return state_dict

