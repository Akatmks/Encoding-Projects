import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsdehalo import edge_cleaner, dehalo_alpha, fine_dehalo
from vsdenoise import bm3d, DFTTest, frequency_merge, MaskMode, MotionMode, MVDirection, MVTools, Prefilter, SADMode
from vsdirty import bore
from vsexprtools import norm_expr
from vsmasktools import FreyChen, Morpho, Scharr
from vsmuxtools import settings_builder_5fish_svt_av1_psy, Setup, SVTAV1
from vsTAAmbk import TAAmbk
from vsrgtools import bilateral
from vstools import core, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, join, SPath
from vsrgtools import remove_grain, repair

from sources import sources



assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources



print(f"\033[1mSource:\033[0m \t{sources[episode].source.name}")
src = src_sd = initialize_clip(core.bs.VideoSource(sources[episode].source, showprogress=False))

src_s = initialize_clip(core.bs.VideoSource(sources[episode].source_s, showprogress=False))
diff_s = src.std.PlaneStats(src_s, prop="Luma")
for fr in diff_s[:2000].frames():
    assert fr.props["LumaDiff"] == 0
else:
    print(f"\t\tSource check complete")

if sources[episode].op:
    assert sources[episode].op_type
    op_src = []
    assert sources[episode].op[0] + sources[episode].op_offset + 2157 <= sources[episode].op[1]
    op_src.append(src[sources[episode].op[0]+sources[episode].op_offset:
                      sources[episode].op[0]+sources[episode].op_offset+2157])
    for op_ep in reversed(sources):
        if op_ep != episode and sources[op_ep].op and sources[op_ep].op_type == sources[episode].op_type:
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source, showprogress=False))[sources[op_ep].op[0]+sources[op_ep].op_offset:
                                                                                                          sources[op_ep].op[0]+sources[op_ep].op_offset+2157])

            if len(op_src) >= 6:
                break

    if len(op_src) > 1:
        for fno, fr in enumerate(core.vszip.PlaneMinMax(core.akarin.Expr([op_src[0], op_src[-1]], ["x y - abs", ""]), prop="Luma")[::49].frames()):
            assert fr.props["LumaMax"] <= 64 << 8, f"{fno * 49}"
        else:
            print(f"\t\tfrequency_merge source check complete")

    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))

    # if sources[episode].op_offset > 0:
    #     src = insert_clip(src, op_merge[0] * sources[episode].op_offset, sources[episode].op[0])
    src = insert_clip(src, op_merge, sources[episode].op[0] + sources[episode].op_offset)
    filled_frames = sources[episode].op[0] + sources[episode].op_offset + 2157
    if filled_frames < sources[episode].op[1]:
        src = insert_clip(src, op_merge[2152:sources[episode].op[1]-filled_frames+2152], filled_frames)

src = bore(src, ythickness=(2, 2, 2, 2))



mv = MVTools(src, search_clip=Prefilter.DFTTEST)

mv.analyze(tr=3, blksize=32, overlap=16, truemotion=MotionMode.COHERENCE, divide=2)
mv.recalculate(thsad=60, blksize=8, overlap=4, dct=SADMode.ADAPTIVE_SATD_DCT, truemotion=MotionMode.COHERENCE)

dg_dn_ref = DFTTest().denoise(src, {0.00:0.25, 0.20:0.50, 0.40:1.25, 0.60:6.00, 0.80:18.00, 1.00:30.00}, tr=1, planes=[0])
dg_dn = bm3d(src, sigma=2.00, profile=bm3d.Profile.LOW_COMPLEXITY, tr=0, refine=1, ref=dg_dn_ref, planes=[0])

dg = mv.degrain(dg_dn, src, tr=3, thsad=200, thscd=(500, 2))

sad_forward = mv.mask(src, direction=MVDirection.FORWARD, delta=1, kind=MaskMode.SAD, ml=1000, gamma=5, thscd=(500, 2))
sad_forward = sad_forward.std.PlaneStats(plane=0, prop="SAD")
sad_backward = mv.mask(src, direction=MVDirection.BACKWARD, delta=1, kind=MaskMode.SAD, ml=1000, gamma=5, thscd=(500, 2))
sad_backward = sad_backward.std.PlaneStats(plane=0, prop="SAD")
luma_filter = src.akarin.Expr("x 50000 > 65535 0 ?")
luma_filter = luma_filter.std.PlaneStats(plane=0, prop="HighLuma")
luma_filter = luma_filter.akarin.PropExpr(lambda: dict(HighLumaAverage="1 x.HighLumaAverage - 65535 *"))
sad = core.akarin.Expr([sad_forward, sad_backward, luma_filter], ["""
z
    z.HighLumaAverage
    x.SADMax 0 =
        y
        y.SADMax 0 =
            x
            x y + 0.5 * ? ? ?
""", ""])
sad = sad.std.PlaneStats(plane=0, prop="SAD")
sad = sad.akarin.PropExpr(lambda: dict(SADAverage="""
x.SADAverage 0.5 - 0 max 2 *
1 swap - dup * 1 swap -
"""))
sad = sad.akarin.PropExpr(lambda: dict(OneMinusSADAverage="1 x.SADAverage -",
                                       HalfSADAverage="x.SADAverage 0.5 *",
                                       OneMinusHalfSADAverage="1 x.SADAverage 0.5 * -"))
dg_final = core.akarin.Expr([dg, dg_dn, sad], ["x z.OneMinusSADAverage * y z.SADAverage * +", "x z.OneMinusHalfSADAverage * y z.HalfSADAverage * +"])



dg_y = get_y(dg_final)
aa_mask = FreyChen().edgemask(dg_y)
aa_mask = aa_mask.akarin.Expr("x 3000 - 10 *")
aa_mask = Morpho.inflate(aa_mask, iterations=1)

aa = TAAmbk(dg_y, aatype="Eedi2", mclip=aa_mask)
aaf = dg_y.fmtc.resample(kernel="gaussian", a1=65, fh=0.80, fv=0.80)
aa = core.akarin.Expr([dg_y, aa, aaf, aa_mask], "x y z - a 65536 / * +")
aa = join(aa, dg_final)



dh_mask = fine_dehalo.mask(aa, edgemask=FreyChen(), thmi=15, thma=100, thlimi=35, thlima=90, rx=1, ry=1)
dh_mask_inclusive = fine_dehalo.mask(aa, edgemask=FreyChen(), thmi=15, thma=100, thlimi=35, thlima=70, rx=1, ry=1, edgeproc=1.0, exclude=False)
dh_mask = core.akarin.Expr([dh_mask, dh_mask_inclusive], "x 0.70 * y 0.60 * +")

dh = dehalo_alpha(aa, brightstr=0.84, darkstr=0.03, highsens=25)

dh = core.std.MaskedMerge(aa, dh, dh_mask)

dh_final_ref = bilateral(aa, ref=dh, sigmaR=0.013, sigmaS=8, planes=[0])
dh_final = norm_expr([aa, dh, dh_final_ref], ["y z < y 0.35 * z 0.65 * + x min y ?", ""])

dh_mask_uv = fine_dehalo.mask(aa, edgemask=Scharr(), thlimi=70, thlima=120, rx=1, ry=1)
dh_uv = edge_cleaner(dh_final, strength=9, planes=[1, 2])
dh_uv = core.std.MaskedMerge(dh_final, dh_uv, dh_mask_uv)



final = finalize_clip(dh_uv, dither_type=DitherType.NONE)



if "__main__" in dir(__main__):
    Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")

    output = SPath("Video") / f"{episode}.ivf"
    fgs_table = SPath("grain.tbl")

    settings = settings_builder_5fish_svt_av1_psy(
        preset=2,
        crf=24.80,
        lineart_psy_bias=3,
        texture_psy_bias=4,
        noise_psy_bias=2,
        high_quality_encode_psy_bias=1,
        psy_bias_sharpness_rounding=52,
        texture_ac_bias=3.0,
        texture_energy_bias=1.10,
        fgs_table=str(fgs_table)
    )
    SVTAV1(**settings, sd_clip=src_sd).encode(final, outfile=output)
else:
    final.set_output()
