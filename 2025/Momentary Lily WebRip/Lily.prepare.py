#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

import dfttest2
import json
import vsmasktools
import mvsfunc
from time import time
import vstools
from vstools import core, SPath, vs

source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
keyframes_file = SPath(os.environ["KEYFRAMES_FILE"])
scenes_file = SPath(os.environ["SCENES_FILE"])
if not scenes_file.exists():
    raise FileNotFoundError("Scenes file not found.")
zones_file = SPath(os.environ["ZONES_FILE"])
frame_diff_file = SPath(os.environ["FRAME_DIFF_FILE"])
strong_noise_file = SPath(os.environ["STRONG_NOISE_FILE"])

src = core.lsmas.LWLibavSource(str(source_file))
src = mvsfunc.Depth(src, 16)

if not keyframes_file.exists():
    vstools.Keyframes.from_clip(src).to_file(keyframes_file)
keyframes = vstools.Keyframes.from_file(keyframes_file)

y = vstools.get_y(src)
diffnext = core.std.PlaneStats(y, y.std.DeleteFrames([0, 1, 2]), prop="Next")
diffprev = core.std.PlaneStats(y, y[0] * 3 + y, prop="Prev")

y = vstools.get_y(src)
mask1 = vsmasktools.luma_credit_mask(y, thr=0.88)
y = y.std.Invert()
mask2 = vsmasktools.luma_credit_mask(y, thr=0.88)

y = vstools.get_y(src)
y = dfttest2.DFTTest(y, slocation=[0.0,0.5 , 0.4,0.5 , 0.6,5.0 , 1.0,5.0], tbsize=1)
dn = dfttest2.DFTTest(y, sigma=100, tbsize=1)
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

collect = core.akarin.PropExpr([strong_noise, weak_noise, diffnext, diffprev], lambda: dict(StrongNoiseAverage="x.StrongNoiseAverage", WeakNoiseAverage="y.WeakNoiseAverage", FrameDiff="z.NextDiff a.PrevDiff min"))

with scenes_file.open("r") as f:
    scenes = json.load(f)

with zones_file.open("w") as zones:
    with frame_diff_file.open("w") as frame_diff:
        with strong_noise_file.open("w") as strong_noise:
            start = time()

            scenes_head = 0
            strong_noise_scene_total = 0
            weak_noise_scene_total = 0

            keyframes_head = 0
            frame_diff_keyframe_total = 0
            strong_noise_keyframe_total = 0

            for fno, frame in enumerate(collect.frames(close=True)):
                print(f"Preparing Frame {fno} ({fno / (time() - start):.02f} fps)...", end="\r", file=sys.stderr)

                strong_noise_scene_total += frame.props["StrongNoiseAverage"]
                weak_noise_scene_total += frame.props["WeakNoiseAverage"]

                if fno >= scenes["scenes"][scenes_head]["end_frame"] - 1:
                    strong_noise_scene_average = strong_noise_scene_total / (scenes["scenes"][scenes_head]["end_frame"] - scenes["scenes"][scenes_head]["start_frame"])
                    weak_noise_scene_average = weak_noise_scene_total / (scenes["scenes"][scenes_head]["end_frame"] - scenes["scenes"][scenes_head]["start_frame"])

                    # Strong boost
                    if strong_noise_scene_average < 0.03 and weak_noise_scene_average < 0.06:
                        zones.write(f"{scenes["scenes"][scenes_head]["start_frame"]} {scenes["scenes"][scenes_head]["end_frame"]} svt-av1 reset --lp 4 --keyint -1 --lookahead 120 --input-depth 10 --preset 1 --tune 3 --rc 0 --aq-mode 2 --crf 21 --qm-min 8 --sharpness 1 --film-grain 0 --enable-variance-boost 1 --variance-boost-strength 3 --variance-octile 4 --enable-tf 1 --enable-dlf 1 --enable-cdef 1 --enable-restoration 1 --psy-rd 1.0 --spy-rd 1 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0\n")
                    # Weak boost
                    elif strong_noise_scene_average < 0.05 and weak_noise_scene_average < 0.11:
                        zones.write(f"{scenes["scenes"][scenes_head]["start_frame"]} {scenes["scenes"][scenes_head]["end_frame"]} svt-av1 reset --lp 4 --keyint -1 --lookahead 120 --input-depth 10 --preset 1 --tune 3 --rc 0 --aq-mode 2 --crf 27 --qm-min 8 --sharpness 0 --film-grain 2 --film-grain-denoise 0 --enable-variance-boost 1 --variance-boost-strength 1 --variance-octile 6 --enable-tf 1 --enable-dlf 1 --enable-cdef 1 --enable-restoration 1 --psy-rd 1.3 --spy-rd 1 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0\n")
                    # Actually a drop
                    else:
                        zones.write(f"{scenes["scenes"][scenes_head]["start_frame"]} {scenes["scenes"][scenes_head]["end_frame"]} svt-av1 reset --lp 4 --keyint -1 --lookahead 120 --input-depth 10 --preset 1 --tune 3 --rc 0 --aq-mode 2 --crf 30 --qm-min 8 --sharpness 1 --film-grain 4 --film-grain-denoise 0 --enable-variance-boost 0 --enable-tf 1 --enable-dlf 1 --enable-cdef 1 --enable-restoration 1 --psy-rd 2.0 --spy-rd 1 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0\n")

                    scenes_head += 1
                    weak_noise_scene_total = 0
                    strong_noise_scene_total = 0

                frame_diff_keyframe_total += frame.props["FrameDiff"]
                strong_noise_keyframe_total += frame.props["StrongNoiseAverage"]

                if keyframes_head + 1 < len(keyframes) and fno >= keyframes[keyframes_head + 1] - 1:
                    frame_diff_keyframe_count = keyframes[keyframes_head + 1] - keyframes[keyframes_head]
                    frame_diff_keyframe_average = frame_diff_keyframe_total / (frame_diff_keyframe_count - 4 if frame_diff_keyframe_count >= 8 else frame_diff_keyframe_count / 2)
                    strong_noise_keyframe_average = strong_noise_keyframe_total / (keyframes[keyframes_head + 1] - keyframes[keyframes_head])

                    for _ in range(keyframes[keyframes_head], keyframes[keyframes_head + 1]):
                        frame_diff.write(f"{frame_diff_keyframe_average:.06f}\n")
                        strong_noise.write(f"{strong_noise_keyframe_average:.06f}\n")

                    keyframes_head += 1
                    frame_diff_keyframe_total = 0
                    strong_noise_keyframe_total = 0
                    
            frame_diff_keyframe_count = collect.num_frames - keyframes[keyframes_head]
            frame_diff_keyframe_average = frame_diff_keyframe_total / (frame_diff_keyframe_count - 4 if frame_diff_keyframe_count >= 8 else frame_diff_keyframe_count / 2)
            strong_noise_keyframe_average = strong_noise_keyframe_total / (collect.num_frames - keyframes[keyframes_head])

            for _ in range(keyframes[keyframes_head], collect.num_frames):
                frame_diff.write(f"{frame_diff_keyframe_average:.06f}\n")
                strong_noise.write(f"{strong_noise_keyframe_average:.06f}\n")

            print(file=sys.stderr)
