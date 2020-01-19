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
# $Id: followup_reader_callback_from_file.py 129886 2015-03-06 00:50:36Z claudio.kopper $
# 
# @file  followup_reader_callback_from_file.py
# @version $Revision: 129886 $
# @date $Date: 2015-03-05 19:50:36 -0500 (Thu, 05 Mar 2015) $
# @author Claudio Kopper
#

from icecube import icetray
from icecube import dataclasses

from .frame_packet_to_i3live_json import i3live_json_to_frame_packet

def followup_reader_callback_from_file(filename):
    """
    trivial reader from a text file containing single-line JSON objects
    """
    file = open(filename)
    
    def func():
        line = file.readline().strip()
        if line == "":
            file.close()
            return None
            
        packet = i3live_json_to_frame_packet(line)
        return packet
    return func
