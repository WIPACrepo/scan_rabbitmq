#!/usr/bin/env python

# do a full circle test - generate .i3 frames (GCDQPQP), write them to a JSON
# text file, read them and check if we receive "GCDQPGCDQP". Also inject an
# artificial event header and see if we get the same result back.

import tempfile
import os

tempdir = tempfile.mkdtemp()
tempfile = os.path.join(tempdir, "followup_data.json")
print("writing to", tempfile)

try:
    magic_number = 12345

    from os.path import expandvars

    from I3Tray import *

    from icecube import icetray
    from icecube import dataclasses
    from icecube import dataio
    from icecube import full_event_followup

    # generate a followup_data JSON file

    tray = I3Tray()

    tray.Add("I3InfiniteSource","source",
        Stream=icetray.I3Frame.Physics,
        Prefix=expandvars("$I3_TESTDATA/GCD/GeoCalibDetectorStatus_2016.57531_V0.i3.gz")
        )

    def inject_header(frame):
        header = dataclasses.I3EventHeader()
        header.start_time=dataclasses.I3Time(2010,inject_header.counter)
        header.event_id = inject_header.counter
        inject_header.counter += 1
        header.run_id = magic_number
        frame["I3EventHeader"] = header
    inject_header.counter = 0
    tray.Add(inject_header, "inject_header")

    tray.Add("QConverter", "make_some_QP_packets",
        WritePFrame=True)

    tray.Add(full_event_followup.I3FullEventFollowupWriter,
        Keys = ["I3EventHeader"],
        WriterCallback = \
            full_event_followup.followup_writer_callback_to_file(tempfile),
        Streams = [
            icetray.I3Frame.Geometry,
            icetray.I3Frame.Calibration,
            icetray.I3Frame.DetectorStatus,
            icetray.I3Frame.DAQ,
            icetray.I3Frame.Physics],
        If = lambda f: True) # do this for all the frames in this example

    tray.Execute(5) # GCD + two QP packets

    del tray


    ####

    # now load the json file and see if we get the right frames back

    tray = I3Tray()

    tray.Add(full_event_followup.I3FullEventFollowupReader,
        ReaderCallback = \
            full_event_followup.followup_reader_callback_from_file(tempfile))

    def record_streams(frame):
        record_streams.stream_list.append(frame.Stop.id)
        if frame.Stop == icetray.I3Frame.Physics:
            record_streams.event_headers.append(frame["I3EventHeader"])
    record_streams.stream_list = []
    record_streams.event_headers = []
    tray.Add(record_streams,
        Streams=[icetray.I3Frame.Geometry,
                 icetray.I3Frame.Calibration,
                 icetray.I3Frame.DetectorStatus,
                 icetray.I3Frame.DAQ,
                 icetray.I3Frame.Physics])

    tray.Execute()

    del tray

    if record_streams.stream_list != ['G','C','D','Q','P','G','C','D','Q','P']:
        print("expected:", ['G','C','D','Q','P','G','C','D','Q','P'])
        print("received:", record_streams.stream_list)
        raise RuntimeError("list of received streams is not GCDQPGCDQP")

    if len(record_streams.event_headers) != 2:
        print("expected:", 2)
        print("received:", len(record_streams.event_headers))
        raise RuntimeError("number of P-frames/event headers is not 2")

    count = 0
    for h in record_streams.event_headers:
        if h.run_id != magic_number:
            print("expected:", magic_number)
            print("received:", h.run_id)
            raise RuntimeError("run_id is not correct")
            
        if h.event_id != count:    
            print("expected:", count)
            print("received:", h.event_id)
            raise RuntimeError("event_id is not correct")
        
        count += 1
finally:
    # clean up (and don't complain if it fails)
    print("cleaning up...")
    try:
        os.remove(tempfile)
        os.rmdir(tempdir)
    except:
        pass

# test passed, return 0
exit(0)
