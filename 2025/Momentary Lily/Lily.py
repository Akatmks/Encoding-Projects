#!/usr/bin/env python3

# VSPipe Lily.py -c y4m - | x264_x64 --threads 20 --demuxer y4m --output-csp i420 --output-depth 8 --crf 19 --preset veryslow --keyint 360 --min-keyint 1 --ref 13 --deblock 1:1 --rc-lookahead 250 --aq-mode 3 --aq-strength 0.8 --qcomp 0.75 --fade-compensate 0.33 --psy-rd 0.4:0.15 --colorprim bt709 --transfer bt709 --colormatrix bt709 --output "../Lily new.264" -

import os
import sys
sys.path.insert(0, os.getcwd())

import adptvgrnMod
import vsdenoise
import vsdehalo
import EoEfunc
from functools import partial
import havsfunc
import vsmasktools
import muvsfunc
import mvsfunc
import vsTAAmbk
import vstools
from vstools import core, SPath, vs

source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
keyframes_file = SPath(os.environ["KEYFRAMES_FILE"])
subtitle_file = SPath(os.environ["SUBTITLE_FILE"])
if not subtitle_file.exists():
    raise FileNotFoundError("Subtitle file not found.")
fonts_dir = SPath(os.environ["FONTS_DIR"])

src = core.lsmas.LWLibavSource(str(source_file))
src = mvsfunc.Depth(src, 16)

if not keyframes_file.exists():
    vstools.Keyframes.from_clip(src).to_file(keyframes_file)
keyframes = vstools.Keyframes.from_file(keyframes_file)

y = vstools.plane(src, 0)
diffnext = core.std.PlaneStats(y, y.std.DeleteFrames([0, 1, 2]), prop="DBNext")
diffprev = core.std.PlaneStats(y, y[0] * 3 + y, prop="DBPrev")

class SceneStats(vstools.SceneBasedDynamicCache):
    class cache(dict[int, tuple[float, float, float]]):
        def __init__(self, clip: vs.VideoNode, keyframes: vstools.Keyframes) -> None:
            self.clip = clip
            self.keyframes = keyframes

        def __getitem__(self, idx: int) -> tuple[float, float, float]:
            if idx not in self:
                frame_range = self.keyframes.scenes[idx]
                cut_clip = self.clip[frame_range.start:frame_range.stop]

                min_max_avg = vstools.clip_data_gather(cut_clip, None, lambda n, f: (float(f.props[f"DBFrameDiff"]),))
                frame = [x[0] for x in min_max_avg]
                self[idx] = (min(frame), max(frame), sum(frame) / len(frame))

            return super().__getitem__(idx)

    def __init__(self, clip: vs.VideoNode, keyframes: vstools.Keyframes | str, cache_size: int = 5) -> None:
        super().__init__(clip, keyframes, cache_size)

        self.prop_keys = tuple(f"DBFrameDiff{key}" for key in ("Min", "Max", "Average"))
        self.scene_avgs = self.__class__.cache(self.clip, self.keyframes)

    def get_clip(self, key: int) -> vs.VideoNode:
        return self.clip.std.SetFrameProps(**dict(zip(self.prop_keys, self.scene_avgs[key])))

avgdiff = core.akarin.PropExpr([diffnext, diffprev], lambda: dict(DBFrameDiff="x.DBNextDiff y.DBPrevDiff min"))
avgdiff = SceneStats.from_clip(avgdiff, keyframes)
eval_1 = avgdiff

db = vsdenoise.dpir.DEBLOCK(src, strength=16)
dn = db.dfttest.DFTTest(slocation=[0.0,5.0 , 0.4,5.0 , 0.6,0.5 , 1.0,0.5], planes=[0], tbsize=1)
dn = dn.dfttest.DFTTest(slocation=[0.0,5.0 , 0.4,5.0 , 0.6,2.0 , 1.0,2.0], planes=[1, 2], tbsize=1)
cat_1 = dn

smd = havsfunc.SMDegrain(src, tr=3, thSAD=35, thSADC=0)
ref = smd.dfttest.DFTTest(slocation=EoEfunc.freq._slocation, planes=[0], **EoEfunc.freq._dfttest_args)
dn = vsdenoise.BM3D(smd, sigma=[0.6, 0], radius=3, ref=ref).final()
dn = dn.dfttest.DFTTest(sigma=2, planes=[1, 2], tbsize=1)
cat_2 = dn

def FrameEval(n, f, cat_1, cat_2):
    if f.props["DBFrameDiffAverage"] >= 0.07:
        return cat_1
    else:
        return cat_2
sec_1 = core.std.FrameEval(src, partial(FrameEval, cat_1=cat_1, cat_2=cat_2), prop_src=[eval_1])

y = vstools.plane(sec_1, 0)
mask0 = vsTAAmbk.mask_prewitt(mthr=2500)(y)
mask1 = vsmasktools.luma_credit_mask(y, thr=0.88)
y = y.std.Invert()
mask2 = vsmasktools.luma_credit_mask(y, thr=0.88)
mask = core.akarin.Expr([mask0, mask1, mask2], "x y z + -")
y = vstools.plane(sec_1, 0)
aa = vsTAAmbk.TAAmbk(y, aatype="Eedi2", sharp=-0.15, dark=0.15, mclip=mask)
aa = core.std.ShufflePlanes(clips=[aa, sec_1], planes=[0, 1, 2], colorfamily=vs.YUV)

dh = vsdehalo.fine_dehalo(aa, brightstr=0.7)
dh = mvsfunc.LimitFilter(dh, aa, thr=1.8, elast=4)
cat_1 = dh

cat_2 = sec_1

def FrameEval(n, f, cat_1, cat_2):
    if f.props["DBFrameDiffAverage"] >= 0.05:
        return cat_1
    else:
        return cat_2
sec_2 = core.std.FrameEval(src, partial(FrameEval, cat_1=cat_1, cat_2=cat_2), prop_src=[eval_1])

sub = sec_2.assrender.TextSub(subtitle_file, fontdir=str(fonts_dir))

cat_1 = adptvgrnMod.adptvgrnMod(sub, strength=0.20, luma_scaling=10, static=True)
cat_2 = adptvgrnMod.adptvgrnMod(sub, strength=0.05, luma_scaling=10, static=True)

sec_3 = core.std.FrameEval(src, partial(FrameEval, cat_1=cat_1, cat_2=cat_2), prop_src=[eval_1])

out = mvsfunc.Depth(sec_3, 8)
out.set_output()
