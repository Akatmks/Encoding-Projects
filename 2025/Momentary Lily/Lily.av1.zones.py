#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

import json
import vsmasktools
import mvsfunc
from time import time
import vstools
from vstools import core, SPath, vs

source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
scenes_file = SPath(os.environ["SCENES_FILE"])
if not scenes_file.exists():
    raise FileNotFoundError("Scenes file not found.")
zones_file = SPath(os.environ["ZONES_FILE"])

src = core.lsmas.LWLibavSource(str(source_file))
src = mvsfunc.Depth(src, 16)

y = vstools.get_y(src)
mask1 = vsmasktools.luma_credit_mask(y, thr=0.88)
y = y.std.Invert()
mask2 = vsmasktools.luma_credit_mask(y, thr=0.88)

y = vstools.get_y(src)
y = y.dfttest.DFTTest(slocation=[0.0,0.5 , 0.4,0.5 , 0.6,5.0 , 1.0,5.0], tbsize=1)
dn = y.dfttest.DFTTest(sigma=100, tbsize=1)
noise = core.akarin.Expr([y, dn, mask1, mask2], "x y - abs z - a -")

strong_noise = noise.akarin.Expr("x 900 >= 65535 0 ?")
strong_noise_subtract = strong_noise
strong_noise = strong_noise.akarin.Expr("""
x[-3,-3] x[-3,-2] x[-3,-1] x[-3,0] x[-3,1] x[-3,2] x[-3,3]
x[-2,-3] x[-2,-2] x[-2,-1] x[-2,0] x[-2,1] x[-2,2] x[-2,3]
x[-1,-3] x[-1,-2] x[-1,-1] x[-1,0] x[-1,1] x[-1,2] x[-1,3]
x[0,-3] x[0,-2] x[0,-1] x[0,0] x[0,1] x[0,2] x[0,3]
x[1,-3] x[1,-2] x[1,-1] x[1,0] x[1,1] x[1,2] x[1,3]
x[2,-3] x[2,-2] x[2,-1] x[2,0] x[2,1] x[2,2] x[2,3]
x[3,-3] x[3,-2] x[3,-1] x[3,0] x[3,1] x[3,2] x[3,3]
sort49 drop36 result! drop12
result@""")
strong_noise = strong_noise.std.PlaneStats(prop="StrongNoise")

strong_noise_subtract = strong_noise_subtract.rgvs.RemoveGrain(2).std.Maximum().std.Maximum().std.Maximum().std.Maximum()
weak_noise = core.akarin.Expr([noise, strong_noise_subtract], "x 400 >= x 900 <= and 65535 y - 0 ?")
weak_noise = weak_noise.akarin.Expr("""
x[-3,-3] x[-3,-2] x[-3,-1] x[-3,0] x[-3,1] x[-3,2] x[-3,3]
x[-2,-3] x[-2,-2] x[-2,-1] x[-2,0] x[-2,1] x[-2,2] x[-2,3]
x[-1,-3] x[-1,-2] x[-1,-1] x[-1,0] x[-1,1] x[-1,2] x[-1,3]
x[0,-3] x[0,-2] x[0,-1] x[0,0] x[0,1] x[0,2] x[0,3]
x[1,-3] x[1,-2] x[1,-1] x[1,0] x[1,1] x[1,2] x[1,3]
x[2,-3] x[2,-2] x[2,-1] x[2,0] x[2,1] x[2,2] x[2,3]
x[3,-3] x[3,-2] x[3,-1] x[3,0] x[3,1] x[3,2] x[3,3]
sort49 drop42 result! drop6
result@""")
weak_noise = weak_noise.std.PlaneStats(prop="WeakNoise")

noise = core.akarin.PropExpr([strong_noise, weak_noise], lambda: dict(StrongNoiseAverage="x.StrongNoiseAverage", WeakNoiseAverage="y.WeakNoiseAverage"))

with scenes_file.open("r") as f:
    scenes = json.load(f)

with zones_file.open("w") as f:
    start = time()
    scenes_head = 0
    strong_noise_total = 0
    strong_noise_count = 0
    weak_noise_total = 0
    weak_noise_count = 0
    for fno, frame in enumerate(noise.frames(close=True)):
        print(f"Zoning Frame {fno} ({fno / (time() - start):.02f} fps)...", end="\r", file=sys.stderr)
        strong_noise_total += frame.props["StrongNoiseAverage"]
        strong_noise_count += 1
        weak_noise_total += frame.props["WeakNoiseAverage"]
        weak_noise_count += 1

        if fno >= scenes["scenes"][scenes_head]["end_frame"] - 1:
            strong_noise_average = strong_noise_total / strong_noise_count
            weak_noise_average = weak_noise_total / weak_noise_count

            # Strong boost
            if strong_noise_average < 0.03 and weak_noise_average < 0.06:
                f.write(f"{scenes["scenes"][scenes_head]["start_frame"]} {scenes["scenes"][scenes_head]["end_frame"]} svt-av1 --preset 1 --tune 3 --rc 0 --crf 21 --aq-mode 2 --qm-min 8 --sharpness 1 --film-grain 0 --enable-variance-boost 1 --variance-boost-strength 3 --variance-octile 4 --enable-tf 2 --enable-dlf 1 --enable-cdef 1 --enable-restoration 1 --psy-rd 1.0 --spy-rd 1\n")
            # Weak boost
            elif strong_noise_average < 0.05 and weak_noise_average < 0.11:
                f.write(f"{scenes["scenes"][scenes_head]["start_frame"]} {scenes["scenes"][scenes_head]["end_frame"]} svt-av1 --preset 1 --tune 3 --rc 0 --crf 27 --aq-mode 2 --qm-min 8 --sharpness 0 --film-grain 1 --film-grain-denoise 0 --enable-variance-boost 1 --variance-boost-strength 1 --variance-octile 6 --enable-tf 2 --enable-dlf 1 --enable-cdef 1 --enable-restoration 1 --psy-rd 1.4 --spy-rd 1\n")
            # Actually a drop
            else:
                f.write(f"{scenes["scenes"][scenes_head]["start_frame"]} {scenes["scenes"][scenes_head]["end_frame"]} svt-av1 --preset 1 --tune 3 --rc 0 --crf 30 --aq-mode 2 --qm-min 8 --sharpness 0 --film-grain 2 --film-grain-denoise 0 --enable-variance-boost 0 --enable-tf 2 --enable-dlf 1 --enable-cdef 1 --enable-restoration 1 --psy-rd 1.8 --spy-rd 1\n")

            weak_noise_total = 0
            weak_noise_count = 0
            strong_noise_total = 0
            strong_noise_count = 0
            scenes_head += 1
    print(file=sys.stderr)
