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
# $Id: __init__.py 129886 2015-03-06 00:50:36Z claudio.kopper $
# 
# @file __init__.py
# @version $Revision: 129886 $
# @date $Date: 2015-03-05 19:50:36 -0500 (Thu, 05 Mar 2015) $
# @author Claudio Kopper
#

# be nice and pull in our dependencies
from icecube import icetray
from icecube import dataclasses 

from .I3FullEventFollowupWriter import I3FullEventFollowupWriter
from .I3FullEventFollowupReader import I3FullEventFollowupReader
from .frame_packet_to_i3live_json import frame_packet_to_i3live_json
from .frame_packet_to_i3live_json import i3live_json_to_frame_packet
from .followup_writer_callback_to_I3String \
    import followup_writer_callback_to_I3String
from .followup_writer_callback_to_file \
    import followup_writer_callback_to_file
from .followup_reader_callback_from_file \
    import followup_reader_callback_from_file
from .create_event_id import create_event_id

# clean up the namespace
del icetray
del dataclasses
