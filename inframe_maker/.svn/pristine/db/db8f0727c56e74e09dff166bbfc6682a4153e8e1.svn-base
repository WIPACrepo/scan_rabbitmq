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
# $Id: I3FullEventFollowupReader.py 129886 2015-03-06 00:50:36Z claudio.kopper $
# 
# @file I3FullEventFollowupReader.py
# @version $Revision: 129886 $
# @date $Date: 2015-03-05 19:50:36 -0500 (Thu, 05 Mar 2015) $
# @author Claudio Kopper
#

from icecube import icetray

class I3FullEventFollowupReader(icetray.I3Module):
    """
    Acts as a driving module / reader.
    This module will use a callback function accepting a full frame packet
    (usually GCDQP). This is *not* meant for standard data processing
    as it circumvents the frame mix-in mechanism on purpose. It can be used
    to feed modules from data from the full-event followup (used for the
    HESE follow-up, for example).
    If the callback function returns None, processing will be stopped.
    """
    
    def __init__(self, context):
        icetray.I3Module.__init__(self, context)
        self.AddParameter("ReaderCallback",
                          "This callback is called without any parameters. " +
                          "It is expected to return a frame packet (vector " +
                          "of frames).",
                          None)
        self.AddOutBox("OutBox")
        
        self.stops_seen_last = []

    def Configure(self):
        self.reader_callback = self.GetParameter("ReaderCallback")

    def Process(self):
        # procure a frame packet from the callback
        frame_packet = self.reader_callback()
        
        if frame_packet is None:
            self.RequestSuspension()
            return
        
        # clear out any frames (circumvent the mix-in mechanism) for
        # frames that do not exist in this packet but might have been
        # seen in a previous one. This should not usually happen in our
        # data (i.e. every packet should have GCDQP).
        stops_in_packet = [frame.Stop.id for frame in frame_packet]
        for stop in self.stops_seen_last:
            if stop not in stops_in_packet:
                # push an empty frame of the correct stream type
                self.PushFrame(icetray.I3Frame(stop))
        self.stops_seen_last = stops_in_packet

        # now just push all frames in order
        for frame in frame_packet:
            self.PushFrame(frame)
