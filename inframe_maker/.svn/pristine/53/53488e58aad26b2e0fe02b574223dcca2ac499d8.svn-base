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
# $Id: followup_writer_callback_to_I3String.py 131778 2015-04-20 19:22:53Z claudio.kopper $
# 
# @file followup_writer_callback_to_I3String.py
# @version $Revision: 131778 $
# @date $Date: 2015-04-20 15:22:53 -0400 (Mon, 20 Apr 2015) $
# @author Claudio Kopper
#
import json

from icecube import icetray
from icecube import dataclasses

from .frame_packet_to_i3live_json import frame_packet_to_i3live_json
from .create_event_id import create_event_id

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def followup_writer_callback_to_I3String(frame_object_name="FollowupMessage", short_message_name=None):
    """
    return a trivial writer callback packaging the JSON block into an I3String
    and storing it in the original frame.
    """
    
    def func(packet, original_frame):
        # attach some basic properties next to the full frames
        if (short_message_name is not None) and (short_message_name in original_frame):
            # a short alert message has been generated before:
            # take it, convert back to a dict and send it along with the frames
            data_plus = json.loads(original_frame[short_message_name].value)
        else:
            # no short alert message has been generated before:
            # send only basic features from the I3EventHeader along with the frames
            data_plus = {}
            data_plus['run_id']    = original_frame["I3EventHeader"].run_id
            data_plus['event_id']  = original_frame["I3EventHeader"].event_id
            data_plus['eventtime'] = str(original_frame["I3EventHeader"].start_time.date_time)
            data_plus['unique_id'] = create_event_id(original_frame["I3EventHeader"].run_id,
                                                     original_frame["I3EventHeader"].event_id)
        msg = frame_packet_to_i3live_json(packet, pnf_framing=False, data_plus = data_plus)
        icetray.logging.log_info(
            "size of packet is {0}".format(sizeof_fmt(len(msg))),
            "test_followup")
        
        original_frame[frame_object_name] = dataclasses.I3String(msg)
    
    return func
