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
# $Id: I3FullEventFollowupWriter.py 131778 2015-04-20 19:22:53Z claudio.kopper $
# 
# @file I3FullEventFollowupWriter.py
# @version $Revision: 131778 $
# @date $Date: 2015-04-20 15:22:53 -0400 (Mon, 20 Apr 2015) $
# @author Claudio Kopper
#

from icecube import icetray

class I3FullEventFollowupWriter(icetray.I3Module):
    """
    Sends a full frame packet (usually GCDQP) for each P-frame to a
    writer callback function provided to the module using the
    "WriterCallback" parameter. Use the "If" parameter to select P-frames to
    send and the "Keys" parameter to define a whitelist of the frame objects
    to include (all objects will be included if unset).
    """
    
    def __init__(self, context):
        icetray.I3Module.__init__(self, context)
        self.AddParameter("Keys",
                          "List of frame key names to send (if not set " +
                          "keys will be sent",
                          None)
        self.AddParameter("WriterCallback",
                          "This callback will receive a list of frames " +
                          "fully defining the P-frame (usually GCDQP). " +
                          "It will also received the original frame for " +
                          "reference (and in case the result needs " +
                          "to be stored in the original frame).",
                          None)
        self.AddParameter("If",
                          "A python function receiving the frame (for " + 
                          "P-frames). If this returns something that " + 
                          "evaluates to True the frame gets processed.",
                          None)
        self.AddParameter("Streams",
                          "Select the streams/stops to work on. Works on " +
                          "all available frames if unset.",
                          None)
        self.AddOutBox("OutBox")
        
        self.stream_order = []
        self.stream_order_set = set()

    def Configure(self):
        self.keys = self.GetParameter("Keys")
        if self.keys is not None:
            self.keys = set(self.keys)
        self.writer_callback = self.GetParameter("WriterCallback")
        self.if_func = self.GetParameter("If")
        self.streams = self.GetParameter("Streams")
        
        if self.streams is not None:
            # convert to a set of stream IDs
            # (since that's what we handle internally)
            stream_list = []
            for stream in self.streams:
                if isinstance(stream, icetray.I3Frame.Stream):
                    stream_list.append(stream.id)
                elif isinstance(stream, str):
                    if len(stream) != 1:
                        icetray.logging.log_fatal(
                            "Streams list includes invalid stream type \"{0}\"".\
                            format(stream), type(self).__name__)
                    stream_list.append(icetray.I3Frame.Stream(stream).id)
            self.streams = set(stream_list)
        
            if icetray.I3Frame.Physics.id not in self.streams:
                icetray.logging.log_fatal(
                    "Streams list parameter does not include Physics frames." +
                    " These are required for this module.",
                    type(self).__name__)
            

    def Process(self):
        frame = self.PopFrame()
        if not frame:
            icetray.logging.log_fatal("no input frame", type(self).__name__)

        if frame.Stop == icetray.I3Frame.Physics:
            if self.if_func is None:
                self.Physics(frame)
            else:
                if self.if_func(frame):
                    self.Physics(frame)
                else:
                    self.PushFrame(frame)
            return
        
        if self.streams is not None:
            if frame.Stop.id not in self.streams:
                # ignore streams we are not supposed to work on
                self.PushFrame(frame)
                return
        
        # record the order of incoming streams
        if frame.Stop.id not in self.stream_order_set:
            # must work on Stop.id (a string) instead of the "Stream" object
            # itself, since the objects are not unique (or the comparison
            # operator is not implemented).
            self.stream_order.append(frame.Stop)
            self.stream_order_set.add(frame.Stop.id)
        
        self.PushFrame(frame)

    def Physics(self, frame):
        # this function needs to make sure to never touch the frame
        # objects in python in order to prevent I3FrameObjects from
        # projects not currently loaded to reach python. The reason is that
        # they cannot be added to a target frame in python.
        # Use the I3Frame merge/purge functions to make full copies of the
        # frames, then purge the non-native I3FrameObjects from each frame.
        
        # create the output frames
        frame_packet = [ icetray.I3Frame(stop) for stop in self.stream_order ]

        # add one P-frame (not part of the stream order)
        frame_packet.append(icetray.I3Frame(icetray.I3Frame.Physics))
        
        # fill frame packet
        for target_frame in frame_packet:
            target_frame.merge(frame) # copy all objects over to new frame
            target_frame.purge() # purge non-native stops in new frame
            
            if self.keys is not None:
                # clean keys we do not want to send
                for key in target_frame.keys():
                    if key not in self.keys:
                        del target_frame[key]
        
        if self.writer_callback is not None:
            self.writer_callback(frame_packet, frame)

        self.PushFrame(frame)
