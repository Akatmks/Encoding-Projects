from vsdehalo import dehalo_sigma, fine_dehalo
from vsdenoise import DFTTest, wnnm
from vskernels import Catrom, Hermite
from vsmasktools import Morpho
import os
from vsrgtools import gauss_blur
import vsTAAmbk
from vstools import core, depth, DitherType, get_y, initialize_clip, SPath


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)


src = src[144:]


dn = wnnm(src, sigma=4.7, tr=1, refine=0, planes=[0])


aa = vsTAAmbk.TAAmbk(dn, mtype="MSharpen", mpand=(2, 1), dark=0.15, cuda=True)

dh = dehalo_sigma(aa, sigma=1.05)
dh_mask = fine_dehalo.mask(aa, rx=1.5, ry=1.5, exclude=False)
dh = core.std.MaskedMerge(aa, dh, dh_mask)

mask_y = get_y(dh)
mask_y = DFTTest().denoise(mask_y, sigma=5.0, tbsize=1)
mask_dn_y = DFTTest().denoise(mask_y, slocation=[0.0,0.0, 0.40,0.0, 0.50,50.0, 1.0,50.0], tbsize=1)
mask_diff_y = core.akarin.Expr([mask_dn_y, mask_y], "x y - abs")
mask_diff_y = gauss_blur(mask_diff_y, sigma=30.0)
mask = mask_diff_y.akarin.Expr("x 120 > 65535 0 ?")
mask = Hermite().scale(mask, width=192, height=108)
mask = Morpho.dilation(mask, iterations=5)
mask = gauss_blur(mask, sigma=2.0)
mask = Catrom().scale(mask, width=1920, height=1080)

final = core.std.MaskedMerge(dh, dn, mask)


out = depth(final, 10, dither_type=DitherType.NONE)


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


out.set_output()
