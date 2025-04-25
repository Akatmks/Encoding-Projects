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
from vsdenoise import dpir
import dfttest2
from functools import partial
from vsmasktools import MinMax, Morpho
from vsscale import ArtCNN, Rescale
from vskernels import Lanczos
import vsTAAmbk
from vstools import core, depth, get_y, initialize_clip, join, SPath, vs


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
error_file = SPath(os.environ["ERROR_FILE"])
if not error_file.exists():
    raise FileNotFoundError("Error file not found.")
frame_diff_file = SPath(os.environ["FRAME_DIFF_FILE"])
if not frame_diff_file.exists():
    raise FileNotFoundError("Frame diff file not found.")

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)

with error_file.open("r") as f:
    error = f.read()
    error = [float(line) for line in error.splitlines()]
with frame_diff_file.open("r") as f:
    frame_diff = f.read()
    frame_diff = [float(line) for line in frame_diff.splitlines()]


y = get_y(src)
db = dpir.DEBLOCK(y, strength=9, tiles=2)
db = join(db, src)

dh = edge_cleaner(db, strength=11)

dn = dfttest2.DFTTest(src, slocation=[0.0,250, 0.3,250, 0.5,50, 1.0,50], tbsize=1, planes=[0])
mask = MinMax.edgemask(get_y(dn))
mask = mask.std.Median()
mask = mask.std.Median()
mask = mask.akarin.Expr(f"x 1200 - 65535 1600 / *")
mask = Morpho.inflate(mask, iterations=1)
merge = core.std.MaskedMerge(db, dh, mask=mask, planes=[0])

diff = core.std.MakeDiff(src, merge, planes=[0])
diff_dn = dfttest2.DFTTest(diff, slocation=[0.0,0.18, 0.5,0.18, 0.7,0.08, 1.0,0.08], tbsize=1, planes=[0])
diff_noise = core.std.MakeDiff(diff, diff_dn, planes=[0])
merge_noise = core.std.MergeDiff(merge, diff_noise, planes=[0])

y = get_y(merge_noise)
aa = vsTAAmbk.TAAmbk(y, aatype="Eedi2", dark=0.10, cuda=True)
aaf = y.fmtc.resample(kernel="gaussian", a1=100, fh=0.80, fv=0.80)
aa = core.akarin.Expr([y, aa, aaf], "x y z - 1.3 * +")
aa = join(aa, merge_noise)

cat_1 = aa

cat_2 = src

dh = fine_dehalo(src, brightstr=0.45, thmi=40, thlimi=110, thlima=210)
aa = based_aa(dh, rfactor=1.5, supersampler=ArtCNN.R8F64(tiles=2))

cat_3 = aa

# This is the wrong kernel. This anime is undescalable
ds = Rescale(src, 871.875, kernel=Lanczos(taps=3)).upscale

diff = core.std.MakeDiff(src, ds, planes=[0])
diff_dn = dfttest2.DFTTest(diff, slocation=[0.0,0.3, 0.4,0.3, 0.6,0.6, 1.0,0.6], tbsize=1, planes=[0])
diff_noise = core.std.MakeDiff(diff, diff_dn, planes=[0])
ds_noise = core.std.MergeDiff(ds, diff_noise, planes=[0])

dh = edge_cleaner(ds_noise, strength=11)

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

cat_4 = merge

def FrameEval(n, cat_1, cat_2, cat_3, cat_4, error):
    if frame_diff[n] > 0.08:
        return cat_1
    elif error[n] > 0.09:
        return cat_2
    elif error[n] > 0.014:
        return cat_3
    else:
        return cat_4
sec_1 = core.std.FrameEval(src, partial(FrameEval, cat_1=cat_1, cat_2=cat_2, cat_3=cat_3, cat_4=cat_4, error=error))


out = sec_1

out = dfttest2.DFTTest(out, slocation=[0.0,0.38, 0.4,0.38, 0.6,0.21, 1.0,0.21], tbsize=1, planes=[0])

out = depth(out, 10)
out.set_output()
