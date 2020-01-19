Code Review for Full_Event_Followup
===================================

Purpose
-------
Pure python code to grap the GCDQP frame series for a given P frame out of PnF 
and send it over to i3Live for fast transmission to the north.

Maintainer
----------
Claudio Kopper

Sponsor
-------
Alex Olivas - Signs off 3/11/15 on r129930

Reviewever
----------
Benedikt Riedel

Review Date
-----------
March 5, 2015

Revision Reviewed
-----------------
129886

General Checks
--------------
* PEP8 Compliance [x]
* Documentation   [x]
* Example Scripts [x]
* Works           [x]

General Comments
----------------

Code is well written, structured, and documented. Pretty clear what is going on: 
I3Frames are pickled and then written into JSON blobs that i3Live understands 
and can transmit. Said blobs are can then be converted back to the I3Frames in 
the north. Come cavets are needed to appease PnF, such as using I3Strings to 
write the pickeled I3Frames to the frame.
