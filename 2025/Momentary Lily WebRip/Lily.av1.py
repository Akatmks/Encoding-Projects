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
    time.sleep(0.5)

import vsdenoise
import vsdehalo
import EoEfunc
import dfttest2
from functools import partial
import havsfunc
import vsmasktools
import mvsfunc
import vsTAAmbk
import vstools
from vstools import core, SPath, vs


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
frame_diff_file = SPath(os.environ["FRAME_DIFF_FILE"])
if not frame_diff_file.exists():
    raise FileNotFoundError("Frame diff file not found.")
strong_noise_file = SPath(os.environ["STRONG_NOISE_FILE"])
if not strong_noise_file.exists():
    raise FileNotFoundError("Strong noise file not found.")

src = core.lsmas.LWLibavSource(str(source_file))
src = mvsfunc.Depth(src, 16)

# This file is biased in Lily.prepare.py
with frame_diff_file.open("r") as f:
    frame_diff = f.read()
    frame_diff = [float(line) for line in frame_diff.splitlines()]

with strong_noise_file.open("r") as f:
    strong_noise = f.read()
    strong_noise = [float(line) for line in strong_noise.splitlines()]


db = vsdenoise.dpir.DEBLOCK(src, strength=16)
dn = dfttest2.DFTTest(db, slocation=[0.0,5.0 , 0.4,5.0 , 0.6,0.5 , 1.0,0.5], planes=[0], tbsize=1)
dn = dfttest2.DFTTest(dn, slocation=[0.0,5.0 , 0.4,5.0 , 0.6,2.0 , 1.0,2.0], planes=[1, 2], tbsize=1)
cat_1 = dn

smd = havsfunc.SMDegrain(src, tr=3, thSAD=35, thSADC=0)
ref = smd.dfttest.DFTTest(slocation=EoEfunc.freq._slocation, planes=[0], **EoEfunc.freq._dfttest_args)
dn = vsdenoise.BM3D(smd, sigma=[1.0, 0], radius=3, ref=ref).final()
dn = dfttest2.DFTTest(dn, sigma=2, planes=[1, 2], tbsize=1)
cat_21 = dn

smd = havsfunc.SMDegrain(src, tr=3, thSAD=35, thSADC=0)
ref = smd.dfttest.DFTTest(slocation=EoEfunc.freq._slocation, planes=[0], **EoEfunc.freq._dfttest_args)
dn = vsdenoise.BM3D(smd, sigma=[0.6, 0], radius=3, ref=ref).final()
dn = dfttest2.DFTTest(dn, sigma=2, planes=[1, 2], tbsize=1)
cat_22 = dn

smd = havsfunc.SMDegrain(src, tr=3, thSAD=35, thSADC=0)
ref = smd.dfttest.DFTTest(slocation=EoEfunc.freq._slocation, planes=[0], **EoEfunc.freq._dfttest_args)
dn = vsdenoise.BM3D(smd, sigma=[0.3, 0], radius=3, ref=ref).final()
dn = dfttest2.DFTTest(dn, sigma=2, planes=[1, 2], tbsize=1)
cat_23 = dn

def FrameEval(n, cat_1, cat_21, cat_22, cat_23, frame_diff, strong_noise):
    if frame_diff[n] >= 0.08:
        return cat_1
    elif frame_diff[n] >= 0.04 and strong_noise[n] >= 0.10:
        return cat_21
    elif strong_noise[n] >= 0.05:
        return cat_22
    else:
        return cat_23
sec_1 = core.std.FrameEval(src, partial(FrameEval, cat_1=cat_1, cat_21=cat_21, cat_22=cat_22, cat_23=cat_23, frame_diff=frame_diff, strong_noise=strong_noise))


y = vstools.get_y(sec_1)
mask0 = vsTAAmbk.mask_prewitt(mthr=3000)(y)
mask1 = vsmasktools.luma_credit_mask(y, thr=0.88)
y = y.std.Invert()
mask2 = vsmasktools.luma_credit_mask(y, thr=0.88)
mask = core.akarin.Expr([mask0, mask1, mask2], "x y z + -")

dh = vsdehalo.edge_cleaner(sec_1)
dh = mvsfunc.LimitFilter(dh, sec_1, thr=1.9, elast=4)

y = vstools.get_y(dh)
aa = vsTAAmbk.TAAmbk(y, aatype="Eedi2", dark=0.12, mclip=mask, cuda=True)
aaf = y.fmtc.resample(kernel="gaussian", a1=85, fh=0.80, fv=0.80)
aa = core.akarin.Expr([y, aa, aaf, mask], "x y z - 1.1 * a * 65536 / +")
aa = core.std.ShufflePlanes(clips=[aa, dh], planes=[0, 1, 2], colorfamily=vs.YUV)

cat_1 = aa

y = vstools.get_y(sec_1)
aa = vsTAAmbk.TAAmbk(y, aatype="Eedi2", dark=0.13, mclip=mask, cuda=True)
aaf = y.fmtc.resample(kernel="gaussian", a1=82, fh=0.80, fv=0.80)
aa = core.akarin.Expr([y, aa, aaf, mask], "x y z - 0.5 * a * 65536 / +")
aa = core.std.ShufflePlanes(clips=[aa, sec_1], planes=[0, 1, 2], colorfamily=vs.YUV)

cat_2 = aa

def FrameEval(n, cat_1, cat_2, frame_diff, strong_noise):
    if frame_diff[n] >= 0.07 or strong_noise[n] >= 0.09:
        return cat_1
    else:
        return cat_2
sec_2 = core.std.FrameEval(src, partial(FrameEval, cat_1=cat_1, cat_2=cat_2, frame_diff=frame_diff, strong_noise=strong_noise))


out = mvsfunc.Depth(sec_2, 10)
out.set_output()
