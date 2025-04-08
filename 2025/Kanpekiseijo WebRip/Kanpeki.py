#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

import rpyc
import time

port = 18860 + int(os.environ["EPISODE"])
c = rpyc.connect("localhost", port)
tid = c.root.register()
while not c.root.request_release(tid):
    time.sleep(0.1)

from vsaa import based_aa
from vsdehalo import edge_cleaner, fine_dehalo
import dfttest2
from functools import partial
from vsmasktools import MinMax, Morpho
from vsscale import Rescale
from vskernels import Lanczos
from vstools import core, depth, get_y, initialize_clip, SPath, vs


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
error_file = SPath(os.environ["ERROR_FILE"])
if not error_file.exists():
    raise FileNotFoundError("Error file not found.")

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)

with error_file.open("r") as f:
    error = f.read()
    error = [float(line) for line in error.splitlines()]


cat_1 = src

dh = fine_dehalo(src, brightstr=0.48, thmi=40, thlimi=190, thlima=240)
aa = based_aa(dh, rfactor=1.6)

cat_2 = aa

# This is the wrong kernel. This anime is undescalable
ds = Rescale(src, 871.875, kernel=Lanczos(taps=3)).upscale

diff = core.std.MakeDiff(src, ds, planes=[0])
diff_dn = dfttest2.DFTTest(diff, slocation=[0.0,0.3, 0.4,0.3, 0.6,0.6, 1.0,0.6], tbsize=1, planes=[0])
diff_noise = core.std.MakeDiff(diff, diff_dn, planes=[0])
ds_noise = core.std.MergeDiff(ds, diff_noise, planes=[0])

dh = edge_cleaner(ds_noise, strength=10)

diff = core.std.MakeDiff(src, dh, planes=[0]) # Not typo
diff_dn = dfttest2.DFTTest(diff, slocation=[0.0,0.22, 0.4,0.22, 0.6,0.16, 0.8,0.0, 1.0,0.0], tbsize=1, planes=[0])
diff_noise = core.std.MakeDiff(diff, diff_dn, planes=[0])
dh_noise = core.std.MergeDiff(dh, diff_noise, planes=[0])

dn = dfttest2.DFTTest(src, slocation=[0.0,250, 0.3,250, 0.5,50, 1.0,50], tbsize=1, planes=[0])
mask = MinMax.edgemask(get_y(dn))
mask = mask.std.Median()
mask = mask.std.Median()
mask = mask.akarin.Expr(f"x 1200 - 65535 1600 / *")
mask = Morpho.inflate(mask, iterations=1)
merge = core.std.MaskedMerge(src, dh_noise, mask=mask, planes=[0])

cat_3 = merge

def FrameEval(n, cat_1, cat_2, cat_3, error):
    if error[n] > 0.07:
        return cat_1
    elif error[n] > 0.014:
        return cat_2
    else:
        return cat_3
sec_1 = core.std.FrameEval(src, partial(FrameEval, cat_1=cat_1, cat_2=cat_2, cat_3=cat_3, error=error))


out = sec_1

out = dfttest2.DFTTest(out, slocation=[0.0,0.38, 0.4,0.38, 0.6,0.2, 1.0,0.2], tbsize=1, planes=[0])

out = depth(out, 10)
out.set_output()
