import awsmfunc as awf
from vsdeband import deband_detail_mask, f3k_deband
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


source_file = SPath(source)
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)


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


db1 = final_dn.msmoosh.MSmooth()
db1_mask = deband_detail_mask(final_dn)
db1_mask = Morpho.inflate(db1_mask, radius=4)
db1 = core.std.MaskedMerge(db1, final_dn, db1_mask)
db2 = f3k_deband(db1, radius=20, thr=130, grain=0.0, dynamic_grain=False, planes=[0])
db2 = f3k_deband(db2, radius=10, thr=260, grain=0.0, dynamic_grain=False, planes=[0])
db2 = f3k_deband(db2, radius=5, thr=260, grain=0.15, dynamic_grain=False, planes=[0])
db2 = limit_filter(db2, db1, dark_thr=0.70, bright_thr=0.70, elast=2.5, planes=[0])


final = depth(db2, 10, dither_type=DitherType.NONE)
final.set_output()
