import awsmfunc as awf
from vsdehalo import dehalo_alpha, fine_dehalo
from vsdenoise import bm3d, DFTTest, mc_degrain, Prefilter
from functools import partial
from vskernels import BSpline, Hermite
from vsmasktools import FreyChen, Morpho
from rekt import rektlvls
from vsrgtools import limit_filter
from vsscale import descale_error_mask, Rescale
import vsTAAmbk
from vstools import core, depth, DitherType, initialize_clip, get_y, join, SPath, split


import os

source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)

if "OP_START" in os.environ:
    op_start = int(os.environ["OP_START"])
    op_end = int(os.environ["OP_END"])
else:
    op_start = None
    op_end = None
if "ED_START" in os.environ:
    ed_start = int(os.environ["ED_START"])
    ed_end = int(os.environ["ED_END"])
else:
    ed_start = None
    ed_end = None


# ---------------------------------------------------------------------
# Set the port used by the dispatch server. You can set it to any port
# of your preference, as long as you set it the same in `Server.py`,
# `Server-Shutdown.py` and your filtering vpy script.
port = 18861
# ---------------------------------------------------------------------
# Copy every line in this file to your filtering vpy script. The
# optimal place to paste this is after you've imported vapoursynth and
# all the vsfunc's, and after you've loaded the source file, but before
# any filtering using VRAM is created / performed.
# ---------------------------------------------------------------------

import rpyc
import time

c = rpyc.connect("localhost", port)
tid = c.root.register()
while not c.root.request_release(tid):
    time.sleep(0.1)


edgefix = rektlvls(src, rownum=[1, 3, 1078, 1076], rowval=[-8, 1, -8, 1],
                        colnum=[1, 3, 1918, 1916], colval=[-8, 1, -8, 1])
edgefix = edgefix.edgefixer.Continuity(4, 4, 4, 4)


dn = DFTTest().denoise(edgefix, {0.0:0.3, 0.4:0.4, 0.6:0.8, 1.0:0.8}, tbsize=1, planes=[0])
dn = DFTTest().denoise(dn, {0.0:0.1, 0.4:0.2, 0.6:0.4, 1.0:0.4}, tbsize=1, planes=[1, 2])


dn_y, dn_u, dn_v = split(dn)

mask = FreyChen().edgemask(dn_y)
mask = Morpho.binarize(mask, 0.09)
mask = mask.akarin.Expr("""
x[-2,-2] x[-1,-2] x[0,-2] x[1,-2] x[2,-2]
x[-2,-1] x[-1,-1] x[0,-1] x[1,-1] x[2,-1]
x[-2,0] x[-1,0] x[0,0] x[1,0] x[2,0]
x[-2,1] x[-1,1] x[0,1] x[1,1] x[2,1]
x[-2,2] x[-1,2] x[0,2] x[1,2] x[2,2]
sort25 drop15 result! drop9
result@
""")
mask = Morpho.closing(mask, 2)
mask = Morpho.expand(mask, 1)
src_y = get_y(src)
rs = Rescale(src_y, 540, kernel=BSpline()).rescale
credit_mask = descale_error_mask(src_y, rs, thr=0.15, tr=2)
mask = core.akarin.Expr([mask, credit_mask], "x y -")
aa_y = vsTAAmbk.TAAmbk(dn_y, strength=0.5, aatype="Eedi2", nt=30, cuda=True, mclip=mask, sharp=-1)
aa_y = vsTAAmbk.TAAmbk(aa_y, strength=0.25, aatype="Nnedi3", mclip=mask, sharp=-1)

mask = Hermite().scale(mask, width=960, height=540)
aa_u = vsTAAmbk.TAAmbk(dn_u, strength=0.5, aatype="Eedi2", nt=30, cuda=True, mclip=mask)
aa_v = vsTAAmbk.TAAmbk(dn_v, strength=0.5, aatype="Eedi2", nt=30, cuda=True, mclip=mask)

aa = join(aa_y, aa_u, aa_v)


dh = dehalo_alpha(aa)
mask = fine_dehalo.mask(aa, rx=3, ry=3, thma=136, edgeproc=0.5)
mask = core.akarin.Expr([mask, credit_mask], "x y -")
dh = core.std.MaskedMerge(aa, dh, mask)


com = core.akarin.Expr([edgefix, dn, dh], "x y - z +")


final_y = get_y(com)

final_dn_ref = mc_degrain(final_y, tr=2, thsad=360, prefilter=Prefilter.DFTTEST)
final_dn_y = bm3d(final_y, ref=final_dn_ref, sigma=0.5, profile=bm3d.Profile.LOW_COMPLEXITY)

final_dn_y = limit_filter(final_dn_y, final_y, dark_thr=0.35, bright_thr=1.5, elast=3.5)

final_dn = join(final_dn_y, com)



edgefix_alt = awf.bbmod(src, left=4, right=4, top=4, bottom=4, thresh=[8192, 8192, 8192], blur=[200, 200, 200], planes=[0, 1, 2], scale_thresh=False, cpass2=False)


dn_alt = DFTTest().denoise(edgefix_alt, {0.0:0.3, 0.4:0.4, 0.6:0.8, 1.0:0.8}, tbsize=1, planes=[0])
dn_alt = DFTTest().denoise(dn_alt, {0.0:0.1, 0.4:0.2, 0.6:0.4, 1.0:0.4}, tbsize=1, planes=[1, 2])


dh_alt = dehalo_alpha(dn_alt)
mask_alt = fine_dehalo.mask(dn_alt, rx=3, ry=3, thma=136, edgeproc=0.5)
credit_mask_alt = descale_error_mask(src_y, rs, thr=0.06)
mask_alt = core.akarin.Expr([mask_alt, credit_mask_alt], "x y -")
dh_alt = core.std.MaskedMerge(dn_alt, dh_alt, mask_alt)

com_alt = core.akarin.Expr([edgefix_alt, dn_alt, dh_alt], "x y - z +")
final_alt = com_alt



dn_alt_op = DFTTest().denoise(edgefix_alt, {0.0:0.7, 0.4:0.5, 0.6:3.0, 1.0:3.0}, tbsize=1, planes=[0])
dn_alt_op = DFTTest().denoise(dn_alt_op, {0.0:0.3, 0.4:0.4, 0.6:1.6, 1.0:1.6}, tbsize=1, planes=[1, 2])


dn_y, dn_u, dn_v = split(dn_alt_op)

mask = FreyChen().edgemask(dn_y)
mask = Morpho.binarize(mask, 0.09)
mask = mask.akarin.Expr("""
x[-2,-2] x[-1,-2] x[0,-2] x[1,-2] x[2,-2]
x[-2,-1] x[-1,-1] x[0,-1] x[1,-1] x[2,-1]
x[-2,0] x[-1,0] x[0,0] x[1,0] x[2,0]
x[-2,1] x[-1,1] x[0,1] x[1,1] x[2,1]
x[-2,2] x[-1,2] x[0,2] x[1,2] x[2,2]
sort25 drop15 result! drop9
result@
""")
mask = Morpho.closing(mask, 2)
mask = Morpho.expand(mask, 1)
mask = core.akarin.Expr([mask, credit_mask_alt], "x y -")
aa_y = vsTAAmbk.TAAmbk(dn_y, strength=0.5, aatype="Eedi2", nt=30, cuda=True, mclip=mask, sharp=-1, repair=-20)
aa_y = vsTAAmbk.TAAmbk(aa_y, strength=0.25, aatype="Nnedi3", mclip=mask, sharp=-1, repair=-20)

mask = Hermite().scale(mask, width=960, height=540)
aa_u = vsTAAmbk.TAAmbk(dn_u, strength=0.5, aatype="Eedi2", nt=30, cuda=True, mclip=mask, repair=-20)
aa_v = vsTAAmbk.TAAmbk(dn_v, strength=0.5, aatype="Eedi2", nt=30, cuda=True, mclip=mask, repair=-20)

aa_alt_op = join(aa_y, aa_u, aa_v)


com_alt_op = core.akarin.Expr([edgefix_alt, dn_alt_op, aa_alt_op], "x y - z +")
final_alt_op = com_alt_op



def FrameEval(n, final, final_alt, final_alt_op, op_start, op_end, ed_start, ed_end):
    if op_start is not None and (n >= op_start and n < op_end):
        return final_alt_op
    elif ed_start is not None and (n >= ed_start and n < ed_end):
        return final_alt
    else:
        return final
final = core.std.FrameEval(src, partial(FrameEval, final=final_dn, final_alt=final_alt, final_alt_op=final_alt_op, op_start=op_start, op_end=op_end, ed_start=ed_start, ed_end=ed_end))

final = depth(final, 10, dither_type=DitherType.NONE)
final.set_output()
