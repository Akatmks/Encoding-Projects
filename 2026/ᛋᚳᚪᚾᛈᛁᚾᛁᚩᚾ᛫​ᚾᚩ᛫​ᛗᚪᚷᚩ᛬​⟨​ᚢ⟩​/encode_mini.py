import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsaa import based_aa
from vsdenoise import deblock_qed, DFTTest, frequency_merge
from vskernels import Bilinear
from vsmuxtools import settings_builder_x265, Setup, x265
from vsscale import Rescale
from vsTAAmbk import TAAmbk
from vstools import core, finalize_clip, get_y, initialize_clip, insert_clip, join, replace_ranges, SPath, vs

from sources import sources


assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources


print(f"\033[1mSource:\033[0m \t{sources[episode].source_bd.name}", file=sys.stderr)
src_bd = initialize_clip(core.bs.VideoSource(sources[episode].source_bd))

if sources[episode].source_web:
    print(f"\033[1mSource:\033[0m \t{sources[episode].source_web.name}", file=sys.stderr)
    src_web = initialize_clip(core.bs.VideoSource(sources[episode].source_web))


if sources[episode].source_web:
    print(f"\t\tSource check in progress", file=sys.stderr, end="\r")
    for fno, fr in enumerate(core.vszip.PlaneMinMax(core.akarin.Expr([src_bd, src_web], ["x y - abs", ""]), prop="Luma").frames()):
        if fr.props["LumaMax"] > 72 << 8:
            print(f"\033[1;31m\t\tSource check error on frame {fno}\033[0m", file=sys.stderr)
    else:
        print(f"\t\tSource check complete   ", file=sys.stderr)


if sources[episode].source_web:
    decheckerboard_web = src_web.dctf.DCTFilter(factors=[1, 1, 1, 1, 1, 1, 1, 1,
                                                         1, 1, 1, 1, 1, 1, 1, 1,
                                                         1, 1, 1, 1, 1, 1, 1, 1,
                                                         1, 1, 1, 1, 1, 1, 1, 1,
                                                         1, 1, 1, 1, 1, 1, 1, 1,
                                                         1, 1, 1, 1, 1, 1, 1, 1,
                                                         1, 1, 1, 1, 1, 1, 1, 1,
                                                         1, 1, 1, 1, 1, 1, 1, 0.65])
     
    def high_minmax(clips, **_):
        return core.akarin.Expr(clips, ["""
    x 32768 >= y 32768 >= and
      x y max
      x 32768 <= y 32768 <= and
        x y min
        x ? ?
    """, ""])
    src = frequency_merge(src_bd, decheckerboard_web, lowpass=lambda clip, **kwargs: DFTTest().denoise(clip, **kwargs), mode_low=src_bd, mode_high=high_minmax, planes=[0])
else:
    src = src_bd


if sources[episode].op_type == 1:
    op_src = []
    assert sources[episode].op[1] - sources[episode].op[0] == 2159
    op_src.append(src_bd[sources[episode].op[0]:sources[episode].op[1]])
    for op_ep in sources:
        if op_ep != episode and sources[op_ep].op_type and sources[op_ep].op_type == sources[episode].op_type:
            assert sources[op_ep].op[1] - sources[op_ep].op[0] == 2159
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_bd))[sources[op_ep].op[0]:sources[op_ep].op[1]])

elif sources[episode].op_type == 3:
    op_src = []
    assert sources[episode].op[1] - sources[episode].op[0] >= 2157
    op_src.append(src_bd[sources[episode].op[0]:sources[episode].op[0]+2157])
    for op_ep in sources:
        if op_ep != episode and sources[op_ep].op_type and sources[op_ep].op_type == sources[episode].op_type:
            assert sources[op_ep].op[1] - sources[op_ep].op[0] >= 2157
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_bd))[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])

if sources[episode].op_type in [1, 3]:
    print(f"\t\tfrequency_merge source check in progress", file=sys.stderr, end="\r")
    for fno, fr in enumerate(core.vszip.PlaneMinMax(core.akarin.Expr([op_src[0], op_src[-1]], ["x y - abs", ""]), prop="Luma")[::49].frames()):
        assert fr.props["LumaMax"] <= 64 << 8, f"{fno * 49}"
    else:
        print(f"\t\tfrequency_merge source check complete   ", file=sys.stderr)

    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))

    src = insert_clip(src, op_merge, sources[episode].op[0])


db = deblock_qed(src, (18, 16))
src = replace_ranges(src, db, sources[episode].op, exclusive=True)


src_y = get_y(src)
rs = Rescale(src_y, width=1500, height=843.75, kernel=Bilinear(), downscaler=Bilinear(linear=True))

ds = rs.upscale
re = rs.rescale

ds_sub = core.akarin.Expr([ds, re], "x y -", format=vs.GRAYS)
ds_soften = core.akarin.Expr([ds, re, ds_sub], """
z 0 >
    z[-1,-1] z[0,-1] z[1,-1] z[-1,0] z[0,0] z[1,0] z[-1,1] z[0,1] z[1,1]
    sort9 least1! least2! drop7 least1@ 0 min least2@ 0 min + 0.5 * lim!
    y x - 0.3 * lim@ max x +
    x 0.8 * y 0.2 * + ?
""")

ds_noise = core.akarin.Expr([ds_soften, re, src_y], "z y - x +")
ds_noise = join(ds_noise, src)

aa_opp = TAAmbk(src_y, aatype=2, mclip=src.std.BlankClip(format=vs.GRAY16, color=65535))
aa_opp = core.akarin.Expr([aa_opp, src_y], """
x y - diff!
diff@ 0 =
    0
    diff@ 0 >
        diff@ 200 - 0 max
        diff@ 200 + 0 min ? ?
""", format=vs.GRAYS)
aa_opp = core.akarin.Expr([aa_opp, src_y], """
x 0 =
    y
    x 0 >
    x[0,-1] 0 > x[0,1] 0 > x[-1,0] 0 > x[1,0] 0 >
    or or or and
    x 0 <
    x[0,-1] 0 < x[0,1] 0 < x[-1,0] 0 < x[1,0] 0 <
    or or or and or
        y x +
        y ? ?
""", format=vs.GRAY16)
aa_opp = join(aa_opp, src)

aa_ed = based_aa(src, supersampler=False, mask_thr=80)

lineart_final = ds_noise
if sources[episode].op:
    lineart_final = replace_ranges(lineart_final, aa_opp, sources[episode].op, exclusive=True)
    lineart_final = replace_ranges(lineart_final, src, (sources[episode].op[0] + 1737, sources[episode].op[0] + 2000), exclusive=True)
if sources[episode].ed:
    lineart_final = replace_ranges(lineart_final, aa_ed, sources[episode].ed, exclusive=True)
lineart_final = replace_ranges(lineart_final, src, sources[episode].text, exclusive=True)


from vsdenoise import bm3d, mc_degrain, nl_means

ref = mc_degrain(lineart_final, tr=2, refine=1, thsad=120)
dn_y = bm3d(lineart_final, sigma=0.95, tr=2, profile=bm3d.Profile.LOW_COMPLEXITY, ref=ref, planes=[0])
dn_yuv = nl_means(dn_y, h=0.24, s=1, tr=2, ref=ref, planes=[1, 2])

dn_fine = lineart_final
dn_fine = replace_ranges(dn_fine, dn_yuv, sources[episode].op, exclusive=True)
dn_fine = replace_ranges(dn_fine, dn_y, sources[episode].ed, exclusive=True)

dn_final = DFTTest().denoise(dn_fine, {0.0:0.04, 0.48:0.04, 0.60:0.16, 1.0:0.32}, tr=1, planes=[0])


final = finalize_clip(dn_final)


if "__main__" in dir(__main__):
    setup = Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")
    
    output = SPath("Video") / f"{episode}.mini.265"
    assert final.num_frames <= 50000
    grain = SPath("grain.bin")
    settings = settings_builder_x265(asm="avx512", hist_scenecut="",
                                     tune="grain", crf=19.20, cutree=True, bframe_bias=75, ipratio=1.3, pbratio=1.4, psy_rdoq=3.0,
                                     deblock=[1, 1], aom_film_grain="grain.bin")
    x265(settings, resumable=False, csv=False).encode(final, outfile=output)
else:
    final.set_output()
