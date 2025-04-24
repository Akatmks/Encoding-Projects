#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

import dfttest2
from vskernels import Lanczos
from vsmasktools import FDoGTCanny, normalize_mask
from vsscale import Rescale
from statistics import quantiles
from time import time
from vstools import core, get_y, initialize_clip, Keyframes, SPath, vs


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
keyframes_file = SPath(os.environ["KEYFRAMES_FILE"])
error_file = SPath(os.environ["ERROR_FILE"])
frame_diff_file = SPath(os.environ["FRAME_DIFF_FILE"])

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)

if not keyframes_file.exists():
    Keyframes.from_clip(src).to_file(keyframes_file)
keyframes = Keyframes.from_file(keyframes_file)


y = get_y(src)
dn = dfttest2.DFTTest(y, slocation=[0.0,100, 0.3,100, 0.5,20, 1.0,20], tbsize=1)
diffnext = core.std.PlaneStats(dn, dn.std.DeleteFrames([0, 1]), prop="Next")
diffprev = core.std.PlaneStats(dn, dn[0] * 2 + dn, prop="Prev")

light = get_y(src)
light = light.std.PlaneStats(prop="Light")
# New keyframe if LightMin > 59520 or LightMax < 4736

edge = normalize_mask(FDoGTCanny, get_y(src), sigma=1)
edge = edge.akarin.Expr("x 50000 >= x 0 ?")
edge = edge.std.PlaneStats(prop="Edge")

rescale = Rescale(src, 871.875, kernel=Lanczos(taps=3)).rescale
error = core.akarin.Expr([rescale, get_y(src)], ["x y - abs 500 - 32 *"])
error = error.std.PlaneStats(prop="Error")
error = core.akarin.PropExpr([error, edge], lambda: dict(AverageError="x.ErrorAverage y.EdgeAverage 0.005 > y.EdgeAverage 0.005 ? /"))
# Do nothing if AverageError > 0.07
# fine_dehalo if AverageError > 0.014
# else rescale > edge_cleaner

collect = core.akarin.PropExpr([error, diffnext, diffprev, light], lambda: dict(AverageError="x.AverageError", FrameDiff="y.NextDiff z.PrevDiff min", LightMin="a.LightMin", LightMax="a.LightMax"))


with error_file.open("w") as error_f:
    with frame_diff_file.open("w") as frame_diff_f:
        start = time()

        keyframes_head = 0
        keyframe_start_fno = 0
        error_total = 0
        frame_diff = []

        for fno, frame in enumerate(collect.frames(close=True)):
            print(f"Preparing Frame {fno} ({fno / (time() - start):.02f} fps)...", end="\r", file=sys.stderr)

            if keyframes_head + 1 < len(keyframes) and fno >= keyframes[keyframes_head + 1]:
                error_average = error_total / (fno - keyframe_start_fno)
                frame_diff = frame_diff + [0] * 6
                frame_diff_q3 = quantiles(frame_diff, method="inclusive")[2]

                for _ in range(keyframe_start_fno, fno):
                    error_f.write(f"{error_average:.09f}\n")
                    frame_diff_f.write(f"{frame_diff_q3:.09f}\n")

                keyframes_head += 1
                keyframe_start_fno = fno
                error_total = 0
                frame_diff = []

            elif fno > keyframe_start_fno and (frame.props["LightMin"] > 59520 or frame.props["LightMax"] < 4736):
                error_average = error_total / (fno - keyframe_start_fno)
                frame_diff = frame_diff + [0] * 6
                frame_diff_q3 = quantiles(frame_diff, method="inclusive")[2]

                for _ in range(keyframe_start_fno, fno):
                    error_f.write(f"{error_average:.09f}\n")
                    frame_diff_f.write(f"{frame_diff_q3:.09f}\n")
                    
                keyframe_start_fno = fno
                error_total = 0
                frame_diff = []

            error_total += frame.props["AverageError"]
            frame_diff.append(frame.props["FrameDiff"])

        error_average = error_total / (collect.num_frames - keyframe_start_fno)
        frame_diff = frame_diff + [0] * 6
        frame_diff_q3 = quantiles(frame_diff, method="inclusive")[2]

        for _ in range(keyframe_start_fno, collect.num_frames):
            error_f.write(f"{error_average:.09f}\n")
            frame_diff_f.write(f"{frame_diff_q3:.09f}\n")

        print(file=sys.stderr)
