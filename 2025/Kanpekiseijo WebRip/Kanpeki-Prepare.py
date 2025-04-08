#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from vskernels import Lanczos
from vsmasktools import FDoGTCanny, normalize_mask
from vsscale import Rescale
from time import time
from vstools import core, get_y, initialize_clip, Keyframes, SPath, vs


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
keyframes_file = SPath(os.environ["KEYFRAMES_FILE"])
error_file = SPath(os.environ["ERROR_FILE"])

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)

if not keyframes_file.exists():
    Keyframes.from_clip(src).to_file(keyframes_file)
keyframes = Keyframes.from_file(keyframes_file)


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

collect = core.akarin.PropExpr([error, light], lambda: dict(AverageError="x.AverageError", LightMin="y.LightMin", LightMax="y.LightMax"))


with error_file.open("w") as error_f:
    start = time()

    keyframes_head = 0
    keyframe_start_fno = 0
    error_total = 0

    for fno, frame in enumerate(collect.frames(close=True)):
        print(f"Preparing Frame {fno} ({fno / (time() - start):.02f} fps)...", end="\r", file=sys.stderr)

        if keyframes_head + 1 < len(keyframes) and fno >= keyframes[keyframes_head + 1]:
            error_average = error_total / (fno - keyframe_start_fno)

            for _ in range(keyframe_start_fno, fno):
                error_f.write(f"{error_average:.09f}\n")

            keyframes_head += 1
            keyframe_start_fno = fno
            error_total = 0

        elif fno > keyframe_start_fno and (frame.props["LightMin"] > 59520 or frame.props["LightMax"] < 4736):
            error_average = error_total / (fno - keyframe_start_fno)

            for _ in range(keyframe_start_fno, fno):
                error_f.write(f"{error_average:.09f}\n")
                
            keyframe_start_fno = fno
            error_total = 0

        error_total += frame.props["AverageError"]

    error_average = error_total / (collect.num_frames - keyframe_start_fno)

    for _ in range(keyframe_start_fno, collect.num_frames):
        error_f.write(f"{error_average:.09f}\n")

    print(file=sys.stderr)
