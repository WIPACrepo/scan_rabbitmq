from __future__ import print_function
from __future__ import absolute_import

import numpy
import healpy
import os
import random

import time

from icecube import icetray, dataclasses
from icecube import gulliver, millipede
from icecube import astro
from icecube import VHESelfVeto
from icecube import frame_object_diff
from icecube.frame_object_diff.segments import uncompress
from I3Tray import *

import config

from scan_utils import get_event_mjd
from scan_utils import save_GCD_frame_packet_to_file



class FindBestRecoResultForPixel(icetray.I3Module):
    def __init__(self, ctx):
        super(FindBestRecoResultForPixel, self).__init__(ctx)
        self.AddOutBox("OutBox")
        self.AddParameter("NPosVar", "Number of position variations to collect", 7)

    def Configure(self):
        self.NPosVar = self.GetParameter("NPosVar")

        self.pixelNumToFramesMap = {}

    def Physics(self, frame):
        if "SCAN_HealpixNSide" not in frame:
            raise RuntimeError("SCAN_HealpixNSide not in frame")
        if "SCAN_HealpixPixel" not in frame:
            raise RuntimeError("SCAN_HealpixPixel not in frame")
        if "SCAN_PositionVariationIndex" not in frame:
            raise RuntimeError("SCAN_PositionVariationIndex not in frame")

        nside = frame["SCAN_HealpixNSide"].value
        pixel = frame["SCAN_HealpixPixel"].value
        index = (nside,pixel)
        posVarIndex = frame["SCAN_PositionVariationIndex"].value

        if index not in self.pixelNumToFramesMap:
            self.pixelNumToFramesMap[index] = []
        self.pixelNumToFramesMap[index].append(frame)

        if len(self.pixelNumToFramesMap[index]) >= self.NPosVar:
#            print("all scans arrived for pixel", index)
            bestFrame = None
            bestFrameLLH = None
            for frame in self.pixelNumToFramesMap[index]:
                if "MillipedeStarting2ndPass_millipedellh" in frame:
                    thisLLH = frame["MillipedeStarting2ndPass_millipedellh"].logl
                else:
                    thisLLH = numpy.nan
              #  print("  * llh =", thisLLH)
                if (bestFrame is None) or ((thisLLH < bestFrameLLH) and (not numpy.isnan(thisLLH))):
                    bestFrame=frame
                    bestFrameLLH=thisLLH

            print("all scans arrived for pixel", index, "best LLH is", bestFrameLLH)

            if bestFrame is None:
                # just push the first frame if all of them are nan
                self.PushFrame(self.pixelNumToFramesMap[index][0])
            else:
                self.PushFrame(bestFrame)

            del self.pixelNumToFramesMap[index]

    def Finish(self):
        if len(self.pixelNumToFramesMap) == 0:
            return

        print("**** WARN ****  --  pixels left in cache, not all of the packets seem to be complete")
        print(self.pixelNumToFramesMap)
        print("**** WARN ****  --  END")


def get_reco_losses_inside(p_frame):
    if "MillipedeStarting2ndPass" not in p_frame:
        p_frame["MillipedeStarting2ndPass_totalRecoLossesInside"] = dataclasses.I3Double(numpy.nan)
        p_frame["MillipedeStarting2ndPass_totalRecoLossesTotal"] = dataclasses.I3Double(numpy.nan)
        return
    recoParticle = p_frame["MillipedeStarting2ndPass"]

    if "MillipedeStarting2ndPassParams" not in p_frame:
        p_frame["MillipedeStarting2ndPass_totalRecoLossesInside"] = dataclasses.I3Double(numpy.nan)
        p_frame["MillipedeStarting2ndPass_totalRecoLossesTotal"] = dataclasses.I3Double(numpy.nan)
        return

    def getRecoLosses(vecParticles):
        losses = []
        for p in vecParticles:
            if not p.is_cascade: continue
            if p.energy==0.: continue
            losses.append([p.time, p.energy])
        return losses
    recoLosses = getRecoLosses(p_frame["MillipedeStarting2ndPassParams"])

    intersectionPoints = VHESelfVeto.IntersectionsWithInstrumentedVolume(p_frame["I3Geometry"], recoParticle)
    intersectionTimes = []
    for intersectionPoint in intersectionPoints:
        vecX = intersectionPoint.x - recoParticle.pos.x
        vecY = intersectionPoint.y - recoParticle.pos.y
        vecZ = intersectionPoint.z - recoParticle.pos.z

        prod = vecX*recoParticle.dir.x + vecY*recoParticle.dir.y + vecZ*recoParticle.dir.z
        dist = numpy.sqrt(vecX**2 + vecY**2 + vecZ**2)
        if prod < 0.: dist *= -1.
        intersectionTimes.append(dist/dataclasses.I3Constants.c + recoParticle.time)

    entryTime = None
    exitTime = None
    intersectionTimes = sorted(intersectionTimes)
    if len(intersectionTimes)==0:
        p_frame["MillipedeStarting2ndPass_totalRecoLossesInside"] = dataclasses.I3Double(0.)

        totalRecoLosses = 0.
        for entry in recoLosses:
            totalRecoLosses += entry[1]
        p_frame["MillipedeStarting2ndPass_totalRecoLossesTotal"] = dataclasses.I3Double(totalRecoLosses)
        return

    entryTime = intersectionTimes[0]-60.*I3Units.m/dataclasses.I3Constants.c
    intersectionTimes = intersectionTimes[1:]
    exitTime = intersectionTimes[-1]+60.*I3Units.m/dataclasses.I3Constants.c
    intersectionTimes = intersectionTimes[:-1]

    totalRecoLosses = 0.
    totalRecoLossesInside = 0.
    for entry in recoLosses:
        totalRecoLosses += entry[1]
        if entryTime is not None and entry[0] < entryTime: continue
        if exitTime  is not None and entry[0] > exitTime:  continue
        totalRecoLossesInside += entry[1]

    p_frame["MillipedeStarting2ndPass_totalRecoLossesInside"] = dataclasses.I3Double(totalRecoLossesInside)
    p_frame["MillipedeStarting2ndPass_totalRecoLossesTotal"] = dataclasses.I3Double(totalRecoLosses)


class CollectRecoResults(icetray.I3Module):
    def __init__(self, ctx):
        super(CollectRecoResults, self).__init__(ctx)
        self.AddParameter("event_id", "The event_id", None)
        self.AddParameter("output_dir", "The output_dir", None)
        self.AddOutBox("OutBox")

    def Configure(self):
        self.event_id = self.GetParameter("event_id")
        self.cache_dir = self.GetParameter("output_dir")

        self.this_event_cache_dir = os.path.join(self.cache_dir, self.event_id)

    def Physics(self, frame):
        if "SCAN_HealpixNSide" not in frame:
            raise RuntimeError("SCAN_HealpixNSide not in frame")
        if "SCAN_HealpixPixel" not in frame:
            raise RuntimeError("SCAN_HealpixPixel not in frame")
        if "SCAN_PositionVariationIndex" not in frame:
            raise RuntimeError("SCAN_PositionVariationIndex not in frame")

        nside = frame["SCAN_HealpixNSide"].value
        pixel = frame["SCAN_HealpixPixel"].value
        index = (nside,pixel)

        if "MillipedeStarting2ndPass" not in frame:
            raise RuntimeError("\"MillipedeStarting2ndPass\" not found in reconstructed frame")
        if "MillipedeStarting2ndPass_millipedellh" not in frame:
            llh = numpy.nan
        else:
            llh = frame["MillipedeStarting2ndPass_millipedellh"].logl

        # compute and retrieve losses
        get_reco_losses_inside(frame)
        recoLossesInside = frame["MillipedeStarting2ndPass_totalRecoLossesInside"].value
        recoLossesTotal = frame["MillipedeStarting2ndPass_totalRecoLossesTotal"].value


        # save this frame to the disk

        nside_dir = os.path.join(self.this_event_cache_dir, "nside{0:06d}".format(nside))
        if not os.path.exists(nside_dir):
            os.system("mkdir -p %s"%nside_dir)
        pixel_file_name = os.path.join(nside_dir, "pix{0:012d}.i3".format(pixel))

        print(" - saving pixel file {0}...".format(pixel_file_name))
        save_GCD_frame_packet_to_file([frame], pixel_file_name)

        self.PushFrame(frame)


