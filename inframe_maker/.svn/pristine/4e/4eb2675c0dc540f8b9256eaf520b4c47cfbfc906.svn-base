..
.. Copyright (c) 2015
.. Claudio Kopper <claudio.kopper@icecube.wisc.edu>
.. and the IceCube Collaboration <http://www.icecube.wisc.edu>
..
.. Permission to use, copy, modify, and/or distribute this software for any
.. purpose with or without fee is hereby granted, provided that the above
.. copyright notice and this permission notice appear in all copies.
..
.. THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
.. WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
.. MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
.. SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
.. WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION
.. OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
.. CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
..
..
.. $Id$
..
.. @file index.rst
.. @version $Revision$
.. @date $Date$
.. @author Claudio Kopper
..

.. highlight:: python

.. _full_event_followup-main:

===================
Full Event_Followup
===================

.. toctree::
   :maxdepth: 2

   release_notes
   code_review

Overview
--------

The :doc:`index` roject provides reader and writer modules to convert
single frames into messages suitable for fast followup transmission via iridium
(RUDICS) or I3Live in general. A writer module will work on P-frames, package
them with all their dependent frames (usually GCDQ) and send the result to
a callback function. Callbacks for conversion to JSON suitable for I3Live are
provided. The result can be stored in text files or directly in the original
frame as an I3String. The string, in turn will be read by PnF's onlinewriter
on the fpmaster machine and transmitted to I3Live. All RUDICS/SPADE/email
transmission of messages is handled by i3Live.

A reader module (icetray driving module) is provided to decode the JSON blob
into a frame packet which can then be used for further processing in the North.

The module is agnostic to the input data and will serialize the whole frame
including all GCD information by default. It is meant for HESE event follow-up
work, but can be used for any channel with low rates.

A `Keys` argument can be used to
limit the number of frame objects transmitted. When transmitting GCD
information, this project should be used with a GCD diff/compression scheme
in order to only send differences to a baseline GCD (these should be small
compared to the usual GCD file size of >100MB).
