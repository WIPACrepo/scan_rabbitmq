#
# Copyright (c) 2015
# Claudio Kopper <claudio.kopper@icecube.wisc.edu>
# and the IceCube Collaboration <http://www.icecube.wisc.edu>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION
# OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
#
# $Id: frame_packet_to_i3live_json.py 131778 2015-04-20 19:22:53Z claudio.kopper $
#
# @file frame_packet_to_i3live_json.py
# @version $Revision: 131778 $
# @date $Date: 2015-04-20 15:22:53 -0400 (Mon, 20 Apr 2015) $
# @author Claudio Kopper
#

import json
try:
    import cPickle as pickle
except:
    import pickle
import base64
import zlib

from icecube import icetray

def frame_packet_to_i3live_json(packet, pnf_framing=False, prio=1,
                                service="hese", varname="heseEvent", topic="heseEvent",
                                data_plus = None):
    """
    This will use the boost-serialization-to-pickle interface to serialize
    I3Frames, compress them, base64-encode the result and wrap it all in
    I3Live/Moni2.0-compatible JSON. (or optionally just return it as a
    JSON data payload only in case PnF wants to add the framing.)
    """

    data = {}
    data["frames"] = []
    if data_plus is not None:
        if isinstance(data_plus, dict):
            for key,val in data_plus.items():
                data[key] = val
        else:
            icetray.logging.log_fatal(
                "invalid data_plus object - not a dict",
		"i3live_json_to_frame_packet")
                
    for frame in packet:
        compressed_string = \
            base64.b64encode(
                zlib.compress(
                    pickle.dumps(frame, protocol=2), # Protocol 2 is the last one compatible with python 2.
                                                     # Keep it at that so we can read this with python 2.
                    9
                )
            ).decode('utf-8')
        frame_stop = frame.Stop.id

        data["frames"].append( [frame_stop, compressed_string] )

    if not pnf_framing:
        # return the "raw" data if requested
        # (PnF/pfonlinewriter.py and i3live will add it for us)

        return json.dumps(data)

    payload = dict()
    payload["zmqnotify"] = { "topics": topic }
    payload["data"] = data

    msg = dict()
    msg["prio"] = prio
    msg["service"] = service
    msg["varname"] = varname
    msg["value"] = payload

    return json.dumps(msg)



def i3live_json_to_frame_packet(json_msg, pnf_framing=True):
    """
    Take a JSON packet written by frame_packet_to_i3live_json() and convert
    it back into a frame packet.
    """
    if pnf_framing:
        msg = json.loads(json_msg)

        if not isinstance(msg, dict):
            icetray.logging.log_fatal(
                "invalid JSON packet - not a dict",
                "i3live_json_to_frame_packet")

        if "value" not in msg:
            icetray.logging.log_fatal(
                "invalid JSON packet - no \"value\" key found",
                "i3live_json_to_frame_packet")

        payload = msg["value"]
        del msg

        if "data" not in payload:
            icetray.logging.log_fatal(
                "invalid JSON packet - no \"data\" key found in value dict",
                "i3live_json_to_frame_packet")

        test_data = payload["data"]
        del payload
    else:
        test_data = json.loads(json_msg)
        
    # Check if we read old or new Data format    
    if isinstance(test_data, dict):  ## new format 2018.  useful data in data['frames']
        data = test_data["frames"]
    else:
        data = test_data  ## Old format, data was just a list of frames
    del test_data
        
    frame_packet = []

    for entry in data:
        if len(entry) != 2:
            icetray.logging.log_fatal(
                "invalid JSON packet - more than 2 entries per data item",
                "i3live_json_to_frame_packet")

        decompressed_data = zlib.decompress( base64.b64decode(entry[1]) )
        try:
            frame = pickle.loads(decompressed_data, encoding="bytes")
        except TypeError: # this is the python 2 version
            frame = pickle.loads(decompressed_data)
        del decompressed_data

        if frame.Stop.id != entry[0]:
            icetray.logging.log_error(
                "frame stops inconsistent - frame has {0}, JSON says {1}".\
                format(frame.Stop.id, entry[0]),
                "i3live_json_to_frame_packet")

        frame_packet.append(frame)

    return frame_packet
