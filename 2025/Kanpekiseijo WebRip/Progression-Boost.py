#!/usr/bin/env python3

# Progression Boost
# Copyright (c) Akatsumekusa and contributors
# Thanks to Ironclad and their grav1an, Miss Moonlight and their Lav1e,
# and Trix and their autoboost


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ //////////////////////////////////
# The guide and config starts approximately 40 lines below this. Start
# reading from there.
# ////////////////////////////////// \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------



import os
import sys
sys.path.insert(0, os.getcwd())

import argparse
from collections.abc import Callable
from functools import partial
from itertools import islice
import json
import numpy as np
from pathlib import Path
from scipy.optimize import Bounds, minimize
import subprocess
from time import time
import vapoursynth as vs
from vapoursynth import core

import dfttest2
from vskernels import Lanczos
from vsmasktools import FDoGTCanny, normalize_mask
from vsscale import Rescale
from statistics import quantiles
from vstools import core, depth, get_y, initialize_clip, vs

parser = argparse.ArgumentParser(prog="Progression Boost", description="Boost encoding parameters to maintain a consistent quality throughout the whole encoding", epilog="For more configs, open `Progression-Boost.py` in a text editor and follow the guide at the very top")
parser.add_argument("-i", "--input", type=Path, required=True, help="Source video file")
parser.add_argument("--encode-input", type=Path, help="Source file for test encodes. Supports both video file and vpy file (Default: same as `--input`). This file is only used to perform test encodes, while scene detection will be performed using the video file specified in `--input`, and filtering before metric calculation can be set in the `Progression-Boost.py` file itself")
parser.add_argument("-o", "--output-zones", type=Path, help="Output zones file for encoding")
parser.add_argument("--output-scenes", type=Path, help="Output scenes file for encoding")
parser.add_argument("--output-error", type=Path, required=True, help="Output error file for filtering")
parser.add_argument("--output-frame-diff", type=Path, required=True, help="Output frame diff file for filtering")
parser.add_argument("--temp", type=Path, help="Temporary folder for Progression Boost (Default: output zones or scenes file with file extension replaced by „.boost.tmp“)")
parser.add_argument("-r", "--resume", action="store_true", help="Resume from the temporary folder. By enabling this option, Progression Boost will reuse finished or unfinished testing encodes. This should be disabled should the parameters for test encode be changed")
parser.add_argument("--verbose", action="store_true", help="Progression Boost by default only reports scenes that have received big boost, or scenes that have built unexpected polynomial model. By enabling this option, all scenes will be reported")
args = parser.parse_args()
input_file = args.input
testing_input_file = args.encode_input
if testing_input_file is None:
    testing_input_file = input_file
zones_file = args.output_zones
scenes_file = args.output_scenes
error_file = args.output_error
frame_diff_file = args.output_frame_diff
if not zones_file and not scenes_file:
    parser.print_usage()
    print("Progression Boost: error: at least one of the following arguments is required: -o/--output-zones, --output-scenes")
    raise SystemExit(2)
temp_dir = args.temp
if not temp_dir:
    if zones_file:
        temp_dir = zones_file.with_suffix(".boost.tmp")
    else:
        temp_dir = scenes_file.with_suffix(".boost.tmp")
temp_dir.mkdir(parents=True, exist_ok=True)
testing_resume = args.resume
metric_verbose = args.verbose


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Before everything, the codes above are for commandline arguments.
# The commandline arguments are only for specifying inputs and outputs
# while all encoding settings need to be modified within the script
# starting below.
# 
# To run the script, use `python Progression-Boost.py --input 01.mkv
# --output-zones 01.zones.txt --temp 01.boost.tmp`, or read the help
# for all commandline arguments using `python Progression-Boost.py
# --help`.
#
# On this note, if you don't like anything you see anywhere in this
# script, pull requests are always welcome.
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Have you noticed that we offers multiple presets for Progression
# Boost? The guide and explanations are exactly the same for each
# presets. The difference is only the default value selected. Of course
# as you continue reading, you can always adjust the values for your
# needs.
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Progression Boost will encode the video multiple times to build a
# polynomial model in order to decide on the `--crf` used.
# Specify the `--crf` the test encodes will run at in each pass. The
# number of `--crf`s in this list also decides the number of test
# encodes to perform.
#
# For boosting using SSIMU2 metric using most of the common methods of
# estimating final `--crf`, it's very beneficial to run at least 4
# encode passes. Running 3 passes will only shorten the runtime by one
# fourth, while damaging the consistency of final encode by a huge
# margin. It shouldn't be preferred, unless the main encoding pass is
# also performed at a relatively high `--preset`.
# 
# Also, if you're wondering why the `--crf` values go so high to 40 and
# 50, the answer is that even at 40 or 50, some, especially still,
# scenes can still achieve amazing results with 90+ SSIMU2 mean.
# testing_crfs = np.sort([10.00, 17.00, 27.00, 41.00])

# Boosting using Butteraugli 3Norm metric is different. During our
# testing using SVT-AV1-PSY v2.3.0-Q and v3.0.2, we observed a linear
# relation between `--crf` and Butteraugli 3Norm score in
# `--crf [10 ~ 30]` range. This is both a blessing and a curse. The
# blessing is that we can create a good linear model with only two test
# encode passes. The curse is that we're unable to build a good model
# extending to beyond `--crf 30`, which closes the door to encodes
# targeting lower quality targets. Comment the lines above and
# uncomment the lines below if you want to make a linear model for
# Butteraugli 3Norm targeting lower `--crf`s.
testing_crfs = np.sort([12.00, 20.00])

# Please keep this list sorted and only enter `--crf` values that are
# multiples of 0.25. Progression Boost will break if this requirement
# is not followed.
# ---------------------------------------------------------------------
# Do you want to change other parameters than `--crf` dynamically
# during the test encode? This function receives a `--crf` value and
# should return a string of parameters for the encoder.
#
# If you don't want to change any parameters dynamically, leave this
# function untouched.
def testing_dynamic_parameters(crf: float) -> str:
    return ""
# ---------------------------------------------------------------------
# Specify the `--video-params` or parameters for the encoder during
# test encodes. You should use the same parameters as your final
# encode, except for `--film-grain`, which you may want to set to `0`
# for test encode. You need to specify everything other than `--input`,
# `--output`, `--crf` and the parameters you've set to generate
# dynamically.
testing_parameters = "--lp 4 --keyint -1 --input-depth 10 --preset 6 --fast-decode 1 --tune 3 --qm-min 10 --chroma-qm-min 9 --enable-tf 1 --kf-tf-strength 1 --tf-strength 2 --sharpness 0 --film-grain 0 --psy-rd 2.8 --spy-rd 0 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0"
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Config for the target quality to generate the final `--crf` comes
# later in the config. But before that, specify a hard limit for the
# final `--crf`.
#
# Specify a `--crf` value that's not too far away from the lowest and
# the highest `--crf` value specified in `testing_crfs` to be safe.
# final_min_crf = 6.00
# final_max_crf = 50.00

# If you're using the default `testing_crfs` for Butteraugli 3Norm,
# comment the line above for SSIMU2 and uncomment the lines below.
final_min_crf = 6.00
final_max_crf = 30.00
# ---------------------------------------------------------------------
# Do you want a real constant quality, or do you just want a small
# boost, not wishing to throw a lot of bitrates on the most demanding
# scenes? For targeting constant quality, you don't need to modify
# anything here.
def final_dynamic_crf(crf: float) -> float:
    return crf

# If you want to dampen the most boosted scenes, you can try to
# uncomment the lines below or write your own method.
#
# This function receives `--crf` in multiples of 0.05. The new `--crf`
# it returns can be in any precision.
# Even if you change things here, do not remove `final_min_crf` and 
# `final_max_crf` from last section. They are necessary for Progression
# Boost to work, even if you apply additional limits here.
# def final_dynamic_crf(crf: float) -> float:
#     if crf < testing_crfs[0]:
#         crf = (crf / testing_crfs[0]) ** 0.7 * testing_crfs[0]
#     return crf
# ---------------------------------------------------------------------
# Do you want to change other parameters than `--crf` dynamically
# for the output zones file (and the eventual final encode)? This
# function receives a `--crf` value and should return a string of
# parameters.
#
# An example usage is to lower `--preset` while increase `--crf` a
# little bit for scenes that are boosted to very low `--crf`. However,
# this is not tested, and whether it's worth it is not clear.
#
# If you don't want to change any parameters dynamically, leave this
# function untouched.
def final_dynamic_parameters(crf: float) -> str:
    return ""
# ---------------------------------------------------------------------
# Specify other `--video-params` or parameters for the encoder for the
# output zones file. You should not specify `--crf` or the parameters
# you've set to generate dynamically. You can also choose to not
# specifying anything here and only specify the parameter directly to
# av1an.
final_parameters = "--lp 4 --keyint -1 --input-depth 10 --preset 0 --tune 3 --qm-min 10 --chroma-qm-min 9 --enable-tf 1 --kf-tf-strength 1 --tf-strength 2 --sharpness 0 --film-grain 7 --psy-rd 2.8 --spy-rd 0 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0"
# If you put all your parameters here, you can also enable this option
# to use the reset flag in the zones file.
final_parameters_reset = True
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Specify the desired scene length for scene detection. The result from
# this scene detection pass will be used both for test encodes and the
# final encodes.
scene_detection_extra_split = 240
scene_detection_min_scene_len = 24
# The next setting is only used if WWXD or SCXVID via VapourSynth is
# selected as the scene detection method in the next section.
# WWXD has the tendency to flag too much scenechanges in complex
# everchanging sections. This setting marks the length for a scene for
# the scene detection mechanism to stop dividing it any further.
# However, this does not mean there won't be scenes shorter than this
# setting. It's likely that scenes longer than the this setting will be
# divided into scenes that are shorter than this setting. The hard limit
# is still specified by `scene_detection_min_scene_len`.
# Also, this setting only affects sections where there are a lot of
# scenechanges detected by WWXD. For calmer sections where WWXD doesn't
# flag any scenechanges, the scene detection mechanism will only
# attempt to divide a scene if it is longer than
# `scene_detection_extra_split`, and this setting has no effects.
scene_detection_target_split = 60
# ---------------------------------------------------------------------
# In the grand scheme of scene detection, av1an is the more universal
# option for scene detection. It works well in most conditions.
#
# Depending on the situations, you may want to use `--sc-method fast`
# or `--sc-method standard`.
#
# The reason `--sc-method fast` is often preferred over
# `--sc-method standard` is that `--sc-method standard` will sometimes
# place scenecut not at the actual frame the scene changes, but at a
# frame optimised for encoder to reuse information.
# `--sc-method fast` is preferred because, first, the benefit from this
# optimisation is minimum, and second, it means Progression Boost
# (or any other boosting scripts) will be much less accurate as a
# result, since scenes with such optimisation can contain frames from
# nearby scenes, which said frames will then certainly be overboosted
# or underboosted.
#
# However, in sections that's challenging for scene detection, such as
# a continous cut, many times the length of
# `scene_detection_extra_split`, featuring lots of movements but no
# actual scenecuts, or sections with a lot of very fancy transition
# effects between cuts, `--sc-method standard` should be preferred. The
# additional optimisations work very well for these complex situations.
#
# You should use `--sc-method standard` if you anime contains sections
# challenging for scene detection mentioned above. Otherwise,
# `--sc-method fast` or WWXD or SCXVID based detection introduced below
# should always be preferred.
# 
# If you want to use av1an for scene detection, specify the av1an
# parameters. You need to specify all parameters for an `--sc-only`
# pass other than `-i`, `--temp` and `--scenes`.
# scene_detection_method = "av1an".lower()
# scene_detection_parameters = f"--sc-method fast --chunk-method lsmash"
# Below are the parameters that should always be used. Regular users
# would not need to modify these.
# scene_detection_parameters += f" --sc-only --extra-split {scene_detection_extra_split} --min-scene-len {scene_detection_min_scene_len}"

# av1an is mostly good, except for one single problem: av1an often
# prefers to place the keyframe at the start of a series of still,
# unmoving frames. This preference even takes priority over placing
# keyframes at actual scene changes. For most works, it's common to
# find cuts where the character will make some movements at the very
# start of a cut, before they stops moving and starts talking. Using
# av1an, these few frames will be allocated to the previous scenes.
# These are a low number of frames, with movements, and after an actual
# scene changes, but placed at the very end of previous scene, which is
# why they will often be encoded horrendously. Compared to av1an, WWXD
# or Scxvid is more reliable in this matter, and would have less issues
# like this.
#
# Similar to `--sc-method fast` against `--sc-method standard`, WWXD
# and Scxvid struggles in sections challenging for scene detection. It
# will mark either too much or too few keyframes. This is largely
# alleviated by the additional scene detection logic in this script.
#
# In general, you should always use WWXD or Scxvid if you cares about
# the worst frames. For encodes targeting a good mean quality, if there
# are no sections difficult for scene detection, WWXD or Scxvid is
# preferred over `--sc-method fast`. If there are such sections, as
# explained above when introducing av1an-based scene detection,
# `--sc-method standard` should be preferred.
# 
# Progression Boost provides two options for VapourSynth-based scene
# detection, `wwxd` and `wwxd_scxvid`. `wwxd_scxvid` is slightly safer
# than `wwxd` alone, but it is slower. You should use `wwxd_scxvid`
# unless it's too slow, which `wwxd` can be then used. If you want to
# use VapourSynth-based scene detection, comment the lines above for
# av1an, uncomment the first line below for VapourSynth, and then
# uncomment the specific method you want to use for scene detection.
#
# Note that if you're encoding videos with full instead of limited
# colour range, you must go down to the code and adjust the threshold.
# Search for „limited“, and there will be a comment there marking how
# you should adjust.
scene_detection_method = "vapoursynth".lower()
scene_detection_vapoursynth_method = "wwxd_scxvid".lower() # Preferred
# scene_detection_vapoursynth_method = "wwxd".lower() # Fast
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Specify the av1an parameters for the test encodes. You need to
# specify everything other than `-i`, `-o`, `--temp`, `--resume`,
# `--video-params`, and `--scenes`.
#
# Make sure the number of workers set here suits the number of `--lp`
# specified in `testing_parameters`. As a reference, per BONES and my
# testing, for SVT-AV1-PSY v2.3.0-B, it's optimum to use `--lp 3` and
# `--workers 8` for system with 32 threads, and `--lp 3` and
# `--workers 6` for system with 24 threads.
testing_av1an_parameters = "--workers 4 --chunk-method lsmash --pix-format yuv420p10le --encoder svt-av1 --concat mkvmerge"
# Below are the parameters that should always be used. Regular users
# would not need to modify these.
testing_av1an_parameters += " -y"
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Once the test encodes finish, Progression Boost will start
# calculating metric for each scenes.
# If you want to do some filtering before calculating SSIMU2, you can
# modify the following lines. Otherwise you can leave it unchanged.
metric_reference = core.lsmas.LWLibavSource(input_file.expanduser().resolve(), cachefile=temp_dir.joinpath("source.lwi").expanduser().resolve())
metric_reference = initialize_clip(metric_reference)
metric_reference = dfttest2.DFTTest(metric_reference, slocation=[0.0,0.38, 0.4,0.38, 0.6,0.21, 1.0,0.21], tbsize=1, planes=[0])
metric_reference = depth(metric_reference, 10)
# ---------------------------------------------------------------------
# When calculating metric, we don't need to calculate it for every
# single frame. It's often the case that most frame in the same scene
# are similar to each other.
# Progression Boost by default uses the most basic method of selecting
# one frame every few frames. Use this variable to specify the minimum
# number of frames to be selected and calculated for each scene.
#
# As an example, using the default `12`:
# * When the length of the scene is less than 12 frames, all frames
#   will be calculated.
# * When the length of the scene is between 12 and 23 frames, it's also
#   the case that every frame will be calculated because otherwise
#   skipping half of the frames will result in less than 12 frames
#   being calculated.
# * When the length of the scene is between 24 and 35 frames, every
#   other frame will be calculated. In total, 12 to 17 frames will be
#   calculated.
# 
# Depending on your encoding target, you may want to increase or
# decrease this number. Increasing this number means edge cases would
# have a bigger chance to be included. This is beneficial if you're
# focusing on bad frames. However, if you focus is on getting a good
# mean quality, you should be able to reduce this number a lot.
#
# If you want to not skip any frames in scenes of any length, set this
# to a vale higher than `--extra-split` specified in
# `scene_detection_parameters`.
metric_min_num_frames = 12
# ---------------------------------------------------------------------
# For very long scenes, the logic of `metric_min_num_frames` above
# might end up skipping too many frames.
# As an example, using the default `12` for `metric_min_num_frames` on
# a 360-frame scene, metric will only be calculated every 30 frames.
# To not skip too many frames at a time, specify a maximum `--every`.
metric_max_every = 8
# ---------------------------------------------------------------------
# Progression Boost by default uses the aforementioned basic method of
# selecting one frame every few frames. If you are good with this
# method, you don't need to modify anything here. If you want to use a
# different method, you can implement it here.
#
# This function will be called for the reference clip and the encode
# clip individually.
def metric_process(clip: vs.VideoNode) -> vs.VideoNode:
    every = clip.num_frames // metric_min_num_frames
    every = np.max([1, np.min([metric_max_every, every])])
    clip = clip[:np.ceil(clip.num_frames // every / 2).astype(int) * every:every] + \
           clip[-np.floor(clip.num_frames // every / 2).astype(int) * every + every - 1::every]

# If you want higher speed calculating metrics, here is a hack. What
# about cropping the clip from 1080p to 900p or 720p? This is tested to
# have been working very well, producing very similar final `--crf`s
# while increasing measuring speed significantly. However, since we
# are cropping away outer edges of the screen, for most anime, we will
# have proportionally more characters than backgrounds in the cropped
# compare. This may not may not be preferrable. If you want to enable
# cropping, uncomment the following line to crop the clip to 900p
# before comparing.
#     clip = clip.std.Crop(left=160, right=160, top=90, bottom=90)

    return clip
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# What metric do you want to use? Are you hipping, or are you zipping?
# 
# To use SSIMU2 via vship, uncomment the lines below. 
# metric_calculate = core.vship.SSIMULACRA2
# metric_metric = lambda frame: frame.props["_SSIMULACRA2"]
# metric_better_metric = np.greater

# To use Butteraugli 3Norm via vship, uncomment the lines below.
metric_calculate = core.vship.BUTTERAUGLI
metric_metric = lambda frame: frame.props["_BUTTERAUGLI_3Norm"]
metric_better_metric = np.less

# To use Butteraugli INFNorm via vship, uncomment the lines below.
# metric_calculate = core.vship.BUTTERAUGLI
# metric_metric = lambda frame: frame.props["_BUTTERAUGLI_INFNorm"]
# metric_better_metric = np.less

# To use SSIMU2 via vszip, uncomment the lines below.
# metric_calculate = partial(core.vszip.Metrics, mode=0)
# metric_metric = lambda frame: frame.props["_SSIMULACRA2"]
# metric_better_metric = np.greater
# ---------------------------------------------------------------------
# After calcuating metric for frames, we summarise the quality for each
# scene into a single value. There are two common way for this.
# 
# The first is the percentile method. The percentile method is better
# at making sure that the bad frames are good.
# With an aggressive observation such as observing 10th percentile or
# lower, in tests, we have had the worst single frame to be within 3
# to 4 SSIMU2 away from the mean. Compared to the normal 15 or more
# without boosting, boosting using the percentile method ensures that
# every frame to be decent.
# A note is that if you want to guarantee the best quality, you should
# also increase the number of frames to measured using
# `metric_min_num_frames` variable specified above in order to prevent
# random bad frames from slipping through.
# When targeting lower quality targets, a looser observation such as
# observing the 20th or the 30th percentile should also produce a decent
# result for encodes targeting lower quality targets.
# 
# Note that Progression Boost by default uses median-unbiased estimator
# for calculating percentile, which is much, much more sensitive to
# extreme values than linear estimator.
#
# Specify the `metric_percentile` you want to observe below depending on
# your desired quality for the encode.
# metric_percentile = 20
# def metric_summarise(scores: np.ndarray[float]) -> float:
#     return np.percentile(scores, metric_percentile, method="median_unbiased")

# The percentile method is also tested on Butteraugli 3Norm score, use
# 90th percentile instead of 10th, and 80th percentile instead of 20th,
# and you are good to go.
metric_percentile = 90
def metric_summarise(scores: np.ndarray[float]) -> float:
    return np.percentile(scores, metric_percentile, method="median_unbiased")

# The second method is to calculate a mean value for the whole scene.
# For SSIMU2 score, harmonic mean is studied by Miss Moonlight to have
# good representation of realworld viewing experience, and ensures a
# consistent quality thoughout the encode without bloating too much for
# the worst frames.
# In tests using harmonic mean method, we've observed very small
# standard deviation of less than 2.000 in the final encode, compared to
# a normal value of 3 to 4 without boosting.
#
# To use the harmonic mean method, comment the lines above for the
# percentile method, and uncomment the two lines below.
# def metric_summarise(scores: np.ndarray[float]) -> float:
#     return scores.shape[0] / np.sum(1 / scores)

# For Butteraugli 3Norm score, root mean cube is suggested by Miss
# Moonlight and tested to have good overall boosting result.
#
# To use the root mean cube method, comment the lines above for the
# percentile method, and uncomment the two lines below.
# def metric_summarise(scores: np.ndarray[float]) -> float:
#     return np.mean(scores ** 3) ** (1 / 3)

# If you want to use a different method than above to summarise the
# data, implement your own method here.
# 
# This function is called independently for every scene for every test
# encode.
# def metric_summarise(scores: np.ndarray[float]) -> float:
#     pass
# ---------------------------------------------------------------------
# You don't need to modify anything here.
class UnreliableModelError(Exception):
    def __init__(self, model, message):
        super().__init__(message)
        self.model = model
# ---------------------------------------------------------------------
# For SSIMU2, by default, Progression Boost fit the metric data to a
# constrained cubic polynomial model. If a fit could not be made under
# constraints, an „Unreliable model“ will be reported. You don't need
# to modify anything here unless you want to implement your own method.
# The code here is a little bit long, try scrolling harder if you can't
# reach the next paragraph.
# def metric_model(crfs: np.ndarray[float], quantisers: np.ndarray[float]) -> Callable[[float], float]:
#     if crfs.shape[0] >= 4:
#         polynomial = lambda X, coef: coef[0] * X ** 3 + coef[1] * X ** 2 + coef[2] * X + coef[3]
#         # Mean Squared Error biased towards overboosting
#         objective = lambda coef: np.average((error := (quantisers - polynomial(crfs, coef))) ** 2, weights=metric_better_metric(0, error) + 1.0)
#         if metric_better_metric(quantisers[0] * 1.1, quantisers[0]):
#             bounds = Bounds([-np.inf, -np.inf, -np.inf, -np.inf], [0, np.inf, np.inf, np.inf])
#             constraints = [
#                 # Second derivative 6ax + 2b <= 0 if np.greater
#                 {"type": "ineq", "fun": lambda coef: -(6 * coef[0] * final_min_crf + 2 * coef[1])},
#                 # b^2 - 3ac <= 0
#                 {"type": "ineq", "fun": lambda coef: -(coef[1] ** 2 - 3 * coef[0] * coef[2])}
#             ]
#         else:
#             bounds = Bounds([0, -np.inf, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf])
#             constraints = [
#                 # Second derivative 6ax + 2b >= 0 if np.less
#                 {"type": "ineq", "fun": lambda coef: 6 * coef[0] * final_min_crf + 2 * coef[1]},
#                 # b^2 - 3ac <= 0
#                 {"type": "ineq", "fun": lambda coef: -(coef[1] ** 2 - 3 * coef[0] * coef[2])}
#             ]
#         fit = minimize(objective, [0, *np.polyfit(crfs, quantisers, 2)],
#                        method="SLSQP", options={"ftol": 1e-6}, bounds=bounds, constraints=constraints)
#         if fit.success and not np.isclose(fit.x[0], 0, rtol=0, atol=1e-7):
#             return partial(polynomial, coef=fit.x)
#
#     if crfs.shape[0] >= 3:
#         polynomial = lambda X, coef: coef[0] * X ** 2 + coef[1] * X + coef[2]
#         # Mean Squared Error biased towards overboosting
#         objective = lambda coef: np.average((error := (quantisers - polynomial(crfs, coef))) ** 2, weights=metric_better_metric(0, error) + 1.0)
#         if metric_better_metric(quantisers[0] * 1.1, quantisers[0]):
#             bounds = Bounds([-np.inf, -np.inf, -np.inf], [0, np.inf, np.inf])
#             # First derivative 2ax + b <= 0 if np.greater
#             constraints = [{"type": "ineq", "fun": lambda coef: -(2 * coef[0] * final_min_crf + coef[1])}]
#         else:
#             bounds = Bounds([0, -np.inf, -np.inf], [np.inf, np.inf, np.inf])
#             # First derivative 2ax + b >= 0 if np.less
#             constraints = [{"type": "ineq", "fun": lambda coef: 2 * coef[0] * final_min_crf + coef[1]}]
#         fit = minimize(objective, [0, *np.polyfit(crfs, quantisers, 1)],
#                        method="SLSQP", options={"ftol": 1e-6}, bounds=bounds, constraints=constraints)
#         if fit.success and not np.isclose(fit.x[0], 0, rtol=0, atol=1e-7):
#             return partial(polynomial, coef=fit.x)
#
#     if crfs.shape[0] >= 2:
#         polynomial = lambda X, coef: coef[0] * X + coef[1]
#         # Mean Squared Error biased towards overboosting
#         objective = lambda coef: np.average((error := (quantisers - polynomial(crfs, coef))) ** 2, weights=metric_better_metric(0, error) + 1.0)
#         if metric_better_metric(quantisers[0] * 1.1, quantisers[0]):
#             bounds = Bounds([-np.inf, -np.inf], [0, np.inf])
#         else:
#             bounds = Bounds([0, -np.inf], [np.inf, np.inf])
#         fit = minimize(objective, np.polyfit(crfs, quantisers, 1),
#                        method="L-BFGS-B", options={"ftol": 1e-6}, bounds=bounds)
#         if fit.success and not np.isclose(fit.x[0], 0, rtol=0, atol=1e-7):
#             if not crfs.shape[0] >= 3:
#                 return partial(polynomial, coef=fit.x)
#             else:
#                 def cut(crf):
#                     if crf <= np.average([crfs[-1], final_max_crf], weights=[3, 1]):
#                         return polynomial(crf, fit.x)
#                     else:
#                         return np.nan
#                 return cut
#
#     def cut(crf):
#         for i in range(0, crfs.shape[0]):
#             if crf <= crfs[i]:
#                 return quantisers[i]
#         else:
#             return np.nan
#     raise UnreliableModelError(cut, f"Unable to construct a polynomial model. This may result in overboosting.")

# For Butteraugli 3Norm, as explained in the `testing_crfs` section,
# there appears to be a linear relation between `--crf` and Butteraugli
# 3Norm scores in `--crf [10 ~ 30]` range. For `--crf`s below 10 to 12,
# it seems like the encode quality increases faster than `--crf`
# decreases. The following function accounts for this and deviates from
# the linear regression at `--crf` 12 or lower. The rate used in the
# function is very conservative, in the sense that it will almost only
# overboost than underboost. If you're using the default `testing_crfs`
# for Butteraugli 3Norm, comment the function above for SSIMU2 and
# uncomment the function below.
def metric_model(crfs: np.ndarray[float], quantisers: np.ndarray[float]) -> Callable[[float], float]:
    polynomial = lambda X, coef: coef[0] * X + coef[1]
    # Mean Squared Error biased towards overboosting
    objective = lambda coef: np.average((error := (quantisers - polynomial(crfs, coef))) ** 2, weights=metric_better_metric(0, error) + 1.0)
    if metric_better_metric(quantisers[0] * 1.1, quantisers[0]):
        bounds = Bounds([-np.inf, -np.inf], [0, np.inf])
    else:
        bounds = Bounds([0, -np.inf], [np.inf, np.inf])
    fit = minimize(objective, np.polyfit(crfs, quantisers, 1),
                    method="L-BFGS-B", options={"ftol": 1e-6}, bounds=bounds)
    if fit.success and not np.isclose(fit.x[0], 0, rtol=0, atol=1e-7):
        def predict(crf):
            if crf >= 12:
                return polynomial(crf, fit.x)
            else:
                return polynomial(13 - (13 - crf) ** 1.13, fit.x)
        return predict

    def cut(crf):
        for i in range(0, crfs.shape[0]):
            if crf <= crfs[i]:
                return quantisers[i]
        else:
            return np.nan
    raise UnreliableModelError(cut, f"Test encodes with higher `--crf` received better score than encodes with lower `--crf`. This may result in overboosting.")

# If you want to use a different method, you can implement it here.
#
# This function receives quantisers corresponding to each test encodes
# specified previously in `testing_crfs`, which is provided in the
# first argument `crfs`. It should return a function that will return
# predicted metric score when called with `--crf`.
# You should raise an UnreliableModelError with a model and an error
# message if the model constructed is unreliable. You will have to
# return a model in the exception. If the model constructed is
# unusable, you can use something similar to the `cut` function at the
# end of the two builtin `metric_model` functions.
# def metric_model(crfs: np.ndarray[float], quantisers: np.ndarray[float]) -> Callable[[float], float]:
#     pass
# ---------------------------------------------------------------------
# After calculating the percentile, or harmonic mean, or other
# quantizer of the data, we fit the quantizers to a polynomial model
# and try to predict the lowest `--crf` that can reach the target
# quality we're aiming at.
# Specify the target quality using the variable below.
#
# Note that since we are doing faster test encodes with `--preset 6` by
# default, the quality we get from test encodes will be lower than that
# of the final encode using slower presets. You should account for this
# when setting the number.
metric_target = 0.485
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------


# Scene dectection
scene_detection_scenes_file = temp_dir.joinpath("scenes-detection.scenes.json")

if scene_detection_method == "av1an":
    if not testing_resume or not scene_detection_scenes_file.exists():
        scene_detection_scenes_file.unlink(missing_ok=True)
        command = [
            "av1an",
            "--temp", str(temp_dir.joinpath("scenes-detection.tmp")),
            "-i", str(input_file),
            "--scenes", str(scene_detection_scenes_file),
            *scene_detection_parameters.split()
        ]
        subprocess.run(command, text=True, check=True)
    assert scene_detection_scenes_file.exists()

    with scene_detection_scenes_file.open("r") as scenes_f:
        scenes = json.load(scenes_f)

elif scene_detection_method == "vapoursynth":
    if not testing_resume or not scene_detection_scenes_file.exists():
        assert scene_detection_extra_split >= scene_detection_min_scene_len * 2, "`scene_detection_method` `vapoursynth` does not support `scene_detection_extra_split` to be smaller than 2 times `scene_detection_min_scene_len`."

        scene_detection_clip = core.lsmas.LWLibavSource(input_file.expanduser().resolve(), cachefile=temp_dir.joinpath("source.lwi").expanduser().resolve())
        scene_detection_clip = initialize_clip(scene_detection_clip)

        scene_detection_bits = scene_detection_clip.format.bits_per_sample
        scene_detection_clip = scene_detection_clip.std.PlaneStats(scene_detection_clip[0] + scene_detection_clip, plane=0, prop="Luma")

        y = get_y(scene_detection_clip)
        dn = dfttest2.DFTTest(y, slocation=[0.0,100, 0.3,100, 0.5,20, 1.0,20], tbsize=1)
        diffnext = core.std.PlaneStats(dn, dn.std.DeleteFrames([0, 1]), prop="Next")
        diffprev = core.std.PlaneStats(dn, dn[0] * 2 + dn, prop="Prev")

        edge = normalize_mask(FDoGTCanny, get_y(scene_detection_clip), sigma=1)
        edge = edge.akarin.Expr("x 50000 >= x 0 ?")
        edge = edge.std.PlaneStats(prop="Edge")
        
        rescale = Rescale(scene_detection_clip, 871.875, kernel=Lanczos(taps=3)).rescale
        error = core.akarin.Expr([rescale, get_y(scene_detection_clip)], ["x y - abs 500 - 32 *"])
        error = error.std.PlaneStats(prop="Error")
        error = core.akarin.PropExpr([error, edge], lambda: dict(AverageError="x.ErrorAverage y.EdgeAverage 0.005 > y.EdgeAverage 0.005 ? /"))

        target_width = np.round(np.sqrt(1280 * 720 / scene_detection_clip.width / scene_detection_clip.height) * scene_detection_clip.width / 40) * 40
        if target_width < scene_detection_clip.width * 0.9:
            target_height = np.ceil(target_width / scene_detection_clip.width * scene_detection_clip.height)
            src_height = target_height / target_width * scene_detection_clip.width
            src_top = (scene_detection_clip.height - src_height) / 2
            scene_detection_clip = scene_detection_clip.resize.Point(width=target_width, height=target_height, src_top=src_top, src_height=src_height,
                                                                     format=vs.YUV420P8, dither_type="none")
        scene_detection_clip = scene_detection_clip.wwxd.WWXD()
        try:
            if scene_detection_vapoursynth_method == "wwxd_scxvid":
                scene_detection_clip = scene_detection_clip.scxvid.Scxvid()
        except NameError:
            assert False, "You need to select a `scene_detection_vapoursynth_method` to use `scene_detection_method` `vapoursynth`. Please check your config inside `Progression-Boost.py`."
        
        collect = core.akarin.PropExpr([scene_detection_clip, error, diffnext, diffprev],
                                       lambda: dict(AverageError="y.AverageError", FrameDiff="z.NextDiff a.PrevDiff min"))

        scene_detection_rjust_digits = np.floor(np.log10(collect.num_frames)) + 1
        scene_detection_rjust = lambda frame: str(frame).rjust(scene_detection_rjust_digits.astype(int))

        scenes = {}
        scenes["frames"] = collect.num_frames
        scenes["scenes"] = []

        diffs = np.empty((collect.num_frames,), dtype=float)
        diffs[0] = 1.0
        luma_scenecut_prev = True
        def scene_detection_split_scene(great_diffs, diffs, start_frame, end_frame):
            print(f"Frame [{scene_detection_rjust(start_frame)}:{scene_detection_rjust(end_frame)}] / Creating scenes", end="\r")

            if end_frame - start_frame <= scene_detection_target_split or \
               end_frame - start_frame < 2 * scene_detection_min_scene_len:
                return [start_frame]

            great_diffs_sort = np.argsort(great_diffs)[::-1]

            if end_frame - start_frame <= 2 * scene_detection_target_split:
                for current_frame in great_diffs_sort:
                    if great_diffs[current_frame] < 1.16:
                        break
                    if current_frame - start_frame >= scene_detection_min_scene_len and end_frame - current_frame >= scene_detection_min_scene_len and \
                       current_frame - start_frame <= scene_detection_target_split and end_frame - current_frame <= scene_detection_target_split:
                        return scene_detection_split_scene(great_diffs, diffs, start_frame, current_frame) + \
                               scene_detection_split_scene(great_diffs, diffs, current_frame, end_frame)

            if end_frame - start_frame <= scene_detection_extra_split:
                for current_frame in great_diffs_sort:
                    if great_diffs[current_frame] < 1.16:
                        break
                    if (current_frame - start_frame >= scene_detection_min_scene_len and end_frame - current_frame >= scene_detection_min_scene_len) and \
                       (current_frame - start_frame <= scene_detection_target_split or end_frame - current_frame <= scene_detection_target_split):
                        return scene_detection_split_scene(great_diffs, diffs, start_frame, current_frame) + \
                               scene_detection_split_scene(great_diffs, diffs, current_frame, end_frame)

                for current_frame in great_diffs_sort:
                    if great_diffs[current_frame] < 1.16:
                        return [start_frame]
                    if current_frame - start_frame >= scene_detection_min_scene_len and end_frame - current_frame >= scene_detection_min_scene_len:
                        return scene_detection_split_scene(great_diffs, diffs, start_frame, current_frame) + \
                               scene_detection_split_scene(great_diffs, diffs, current_frame, end_frame)

            else: # end_frame - start_frame > scene_detection_extra_split
                for current_frame in great_diffs_sort:
                    if great_diffs[current_frame] < 1.12:
                        break
                    if (current_frame - start_frame >= scene_detection_min_scene_len and end_frame - current_frame >= scene_detection_min_scene_len) and \
                       np.ceil((current_frame - start_frame) / scene_detection_extra_split).astype(int) + \
                       np.ceil((end_frame - current_frame) / scene_detection_extra_split).astype(int) <= \
                       np.ceil((end_frame - start_frame) / scene_detection_extra_split + 0.15).astype(int):
                        return scene_detection_split_scene(great_diffs, diffs, start_frame, current_frame) + \
                               scene_detection_split_scene(great_diffs, diffs, current_frame, end_frame)
                               
                for current_frame in great_diffs_sort:
                    if great_diffs[current_frame] < 1.16:
                        break
                    if (current_frame - start_frame >= scene_detection_min_scene_len and end_frame - current_frame >= scene_detection_min_scene_len) and \
                       (current_frame - start_frame <= scene_detection_target_split or end_frame - current_frame <= scene_detection_target_split):
                        return scene_detection_split_scene(great_diffs, diffs, start_frame, current_frame) + \
                               scene_detection_split_scene(great_diffs, diffs, current_frame, end_frame)

                for current_frame in great_diffs_sort:
                    if great_diffs[current_frame] < 1.16:
                        break
                    if current_frame - start_frame >= scene_detection_min_scene_len and end_frame - current_frame >= scene_detection_min_scene_len:
                        return scene_detection_split_scene(great_diffs, diffs, start_frame, current_frame) + \
                               scene_detection_split_scene(great_diffs, diffs, current_frame, end_frame)

                diffs_sort = np.argsort(diffs, stable=True)[::-1]

                for current_frame in diffs_sort:
                    if (current_frame - start_frame >= scene_detection_min_scene_len and end_frame - current_frame >= scene_detection_min_scene_len) and \
                       np.ceil((current_frame - start_frame) / scene_detection_extra_split).astype(int) + \
                       np.ceil((end_frame - current_frame) / scene_detection_extra_split).astype(int) <= \
                       np.ceil((end_frame - start_frame) / scene_detection_extra_split).astype(int):
                        return scene_detection_split_scene(great_diffs, diffs, start_frame, current_frame) + \
                               scene_detection_split_scene(great_diffs, diffs, current_frame, end_frame)

            assert False, "This indicates a bug in the original code. Please report this to the repository including this error message in full."

        with error_file.open("w") as error_f:
            with frame_diff_file.open("w") as frame_diff_f:
                start = time()
                
                keyframe_start_frame = 0
                error_total = error.get_frame(0).props["AverageError"]
                frame_diff = [0]

                for current_frame, frame in islice(enumerate(collect.frames(backlog=48)), 1, None):
                    print(f"Frame {current_frame} / Preparing and detecting scenes / {current_frame / (time() - start):.02f} fps", end="\r")

                    if scene_detection_vapoursynth_method == "wwxd":
                        scene_detection_scenecut = frame.props["Scenechange"] == 1
                    elif scene_detection_vapoursynth_method == "wwxd_scxvid":
                        scene_detection_scenecut = (frame.props["Scenechange"] == 1) + (frame.props["_SceneChangePrev"] == 1) / 2
                    else:
                        assert False, "Invalid `scene_detection_vapoursynth_method`. Please check your config inside `Progression-Boost.py`."
                    # Modify here to 251.125 and 3.875 if your source has full instead of limited colour range
                    luma_scenecut = frame.props["LumaMin"] > 231.125 * 2 ** (scene_detection_bits - 8) or \
                                    frame.props["LumaMax"] < 19.875 * 2 ** (scene_detection_bits - 8)

                    if luma_scenecut and not luma_scenecut_prev:
                        diffs[current_frame] = frame.props["LumaDiff"] + 2.0
                    else:
                        diffs[current_frame] = frame.props["LumaDiff"] + scene_detection_scenecut

                    luma_scenecut_prev = luma_scenecut

                    if scene_detection_scenecut > 0.9 or luma_scenecut:
                        error_average = error_total / (current_frame - keyframe_start_frame)
                        frame_diff = frame_diff + [0] * 6
                        frame_diff_q3 = quantiles(frame_diff, method="inclusive")[2]

                        for _ in range(keyframe_start_frame, current_frame):
                            error_f.write(f"{error_average:.09f}\n")
                            frame_diff_f.write(f"{frame_diff_q3:.09f}\n")

                        keyframe_start_frame = current_frame
                        error_total = 0
                        frame_diff = []

                    error_total += frame.props["AverageError"]
                    frame_diff.append(frame.props["FrameDiff"])

                error_average = error_total / (collect.num_frames - keyframe_start_frame)
                frame_diff = frame_diff + [0] * 6
                frame_diff_q3 = quantiles(frame_diff, method="inclusive")[2]

                for _ in range(keyframe_start_frame, collect.num_frames):
                    error_f.write(f"{error_average:.09f}\n")
                    frame_diff_f.write(f"{frame_diff_q3:.09f}\n")

                print(f"Frame {current_frame} / Preparation and scene detection complete / {current_frame / (time() - start):.02f} fps")

        great_diffs = diffs.copy()
        great_diffs[great_diffs < 1.0] = 0
        start_frames = scene_detection_split_scene(great_diffs, diffs, 0, len(diffs)) + [collect.num_frames]
        for i in range(len(start_frames) - 1):
            scenes["scenes"].append({"start_frame": int(start_frames[i]), "end_frame": int(start_frames[i + 1]), "zone_overrides": None})
        print(f"Frame [{scene_detection_rjust(start_frames[i])}:{scene_detection_rjust(start_frames[i + 1])}] / Scene creation complete")
    
        with scene_detection_scenes_file.open("w") as scenes_f:
            json.dump(scenes, scenes_f)

    else:
        with scene_detection_scenes_file.open("r") as scenes_f:
            scenes = json.load(scenes_f)

else:
    assert False, "Invalid `scene_detection_method`."
    

# Testing
for n, crf in enumerate(testing_crfs):
    if not testing_resume or not temp_dir.joinpath(f"test-encode-{n:0>2}.mkv").exists():
        # If you want to use a different encoder than SVT-AV1 derived ones, modify here. This is not tested and may have additional issues.
        command = [
            "av1an",
            "--temp", str(temp_dir.joinpath(f"test-encode-{n:0>2}.tmp")),
            "--keep"
        ]
        if testing_resume:
            command += ["--resume"]
        command += [
            "-i", str(testing_input_file),
            "-o", str(temp_dir.joinpath(f"test-encode-{n:0>2}.mkv")),
            "--scenes", str(scene_detection_scenes_file),
            *testing_av1an_parameters.split(),
            "--video-params", f"--crf {crf:.2f} {testing_dynamic_parameters(crf)} {testing_parameters}"
        ]
        subprocess.run(command, text=True, check=True)
        assert temp_dir.joinpath(f"test-encode-{n:0>2}.mkv").exists()

        temp_dir.joinpath(f"test-encode-{n:0>2}.lwi").unlink(missing_ok=True)


# Metric
metric_encodes = [core.lsmas.LWLibavSource(temp_dir.joinpath(f"test-encode-{n:0>2}.mkv").expanduser().resolve(),
                                           cachefile=temp_dir.joinpath(f"test-encode-{n:0>2}.lwi").expanduser().resolve()) for n in range(len(testing_crfs))]

if zones_file:
    zones_f = zones_file.open("w")

# Ding
metric_iterate_crfs = np.append(testing_crfs, [final_max_crf, final_min_crf])
metric_reporting_crf = testing_crfs[0]

metric_scene_rjust_digits = np.floor(np.log10(len(scenes["scenes"]))) + 1
metric_scene_rjust = lambda scene: str(scene).rjust(metric_scene_rjust_digits.astype(int), "0")
metric_frame_rjust_digits = np.floor(np.log10(metric_reference.num_frames)) + 1
metric_frame_rjust = lambda frame: str(frame).rjust(metric_frame_rjust_digits.astype(int))
metric_scene_frame_print = lambda scene, start_frame, end_frame: f"Scene {metric_scene_rjust(scene)} Frame [{metric_frame_rjust(start_frame)}:{metric_frame_rjust(end_frame)}]"

for i, scene in enumerate(scenes["scenes"]):
    print(f"{metric_scene_frame_print(i, scene["start_frame"], scene["end_frame"])} / Calculating boost", end="\r")
    printing = False

    quantisers = np.empty((len(testing_crfs),), dtype=float)

    reference = metric_reference[scene["start_frame"]:scene["end_frame"]]
    reference = metric_process(reference)
    for n, crf in enumerate(testing_crfs):
        encode = metric_encodes[n][scene["start_frame"]:scene["end_frame"]]
        encode = metric_process(encode)

        scores = np.array([metric_metric(frame) for frame in metric_calculate(reference, encode).frames()])

        quantisers[n] = metric_summarise(scores)

    try:
        model = metric_model(testing_crfs, quantisers)
    except UnreliableModelError as e:
        if not np.all(metric_better_metric(quantisers, metric_target)):
            print(f"{metric_scene_frame_print(i, scene["start_frame"], scene["end_frame"])} / Unreliable model / {str(e)}")
            printing = True
        model = e.model

    final_crf = None
    # This is in fact iterating metric_iterate_crfs, which is constructed above below the Ding comment.
    for n in range(len(testing_crfs) + 1):
        if metric_better_metric(model(metric_iterate_crfs[n]), metric_target):
            if n == len(testing_crfs):
                # This means even at final_max_crf, we are still higher than the target quality.
                # We will just use final_max_crf as final_crf. It shouldn't matter.
                final_crf = metric_iterate_crfs[n]
                break
            else:
                # This means the point where predicted quality meets the target is in higher crf ranges.
                # We will skip this range and continue.
                continue
        else:
            # Because we know from previous iteration that at metric_iterate_crfs[n-1], the predicted quality is higher than the target,
            # and now at metric_iterate_crfs[n], the prediceted quality is lower than the target,
            # this means the point where predicted quality meets the target is within this range between metric_iterate_crfs[n] and metric_iterate_crfs[n-1].
            # The only exception is when n == 0, while will be dealt with later.
            for crf in np.arange(metric_iterate_crfs[n] - 0.05, metric_iterate_crfs[n-1] - 0.005, -0.05):
                if metric_better_metric((value := model(crf - 0.005)), metric_target): # Also numeric instability stuff
                    # We've found the biggest --crf whose predicted quality is higher than the target.
                    final_crf = crf
                    break
            else:
                # The last item in the iteration is metric_iterate_crfs[n-1], and from outer loop we know that at that crf the predicted quality is higher than the target.
                # The only case that this else clause will be reached is at n == 0, that even at metric_iterate_crfs[-1], or final_min_crf, the predicted quality is still below the target the target.
                print(f"{metric_scene_frame_print(i, scene["start_frame"], scene["end_frame"])} / Potential low quality scene / The predicted quality at `final_min_crf` is {value:.3f}, which is worse than `metric_target` at {metric_target:.3f}")
                printing = True
                final_crf = metric_iterate_crfs[n-1]
            
            if final_crf is not None:
                break
    else:
        assert False, "This indicates a bug in the original code. Please report this to the repository including this error message in full."

    final_crf = final_dynamic_crf(final_crf)
    # If you want to use a different encoder than SVT-AV1 derived ones, modify here. This is not tested and may have additional issues.
    final_crf = round(final_crf / 0.25) * 0.25

    if printing or metric_verbose or final_crf < metric_reporting_crf:
        print(f"{metric_scene_frame_print(i, scene["start_frame"], scene["end_frame"])} / OK / Final crf: {final_crf:.2f}")

    if zones_file:
        # If you want to use a different encoder than SVT-AV1 derived ones, modify here. This is not tested and may have additional issues.
        zones_f.write(f"{scene["start_frame"]} {scene["end_frame"]} svt-av1 {"reset" if final_parameters_reset else ""} --crf {final_crf:.2f} {final_dynamic_parameters(final_crf)} {final_parameters}\n")

    if scenes_file:
        scene["zone_overrides"] = {
            "encoder": "svt_av1",
            "passes": 1,
            "video_params": ["--crf", f"{final_crf:.2f}" ] + final_dynamic_parameters(final_crf).split() + final_parameters.split(),
            "photon_noise": None,
            "extra_splits_len": scene_detection_extra_split,
            "min_scene_len": scene_detection_min_scene_len
        }

if zones_file:
    zones_f.close()

if scenes_file:
    with scenes_file.open("w") as scenes_f:
        json.dump(scenes, scenes_f)
print(f"{metric_scene_frame_print(i, scene["start_frame"], scene["end_frame"])} / Boosting complete")
