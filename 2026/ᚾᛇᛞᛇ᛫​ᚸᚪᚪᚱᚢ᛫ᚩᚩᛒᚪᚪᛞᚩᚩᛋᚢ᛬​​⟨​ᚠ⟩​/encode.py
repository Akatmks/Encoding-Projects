import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsaa import based_aa
from vsdeband import pfdeband, placebo_deband
from vsdehalo import dehalo_alpha
from vsdenoise import DFTTest, frequency_merge
from vsmasktools import FreyChen, Morpho
from vsrgtools import bilateral, MeanMode
from vstools import core, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, SPath
from vsmuxtools import settings_builder_5fish_svt_av1_psy, Setup, SVTAV1

from sources import sources



assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources



print(f"Source: \t{sources[episode].source_j.name}", file=sys.stderr)
src = src_sd = initialize_clip(core.bs.VideoSource(sources[episode].source_j, showprogress=False))
src = [src]

if sources[episode].source_d:
    print(f"Source: \t{sources[episode].source_d.name}", file=sys.stderr)
    src.append(initialize_clip(core.bs.VideoSource(sources[episode].source_d, showprogress=False)))

if sources[episode].source_m:
    print(f"Source: \t{sources[episode].source_m.name}", file=sys.stderr)
    src.append(initialize_clip(core.bs.VideoSource(sources[episode].source_m, showprogress=False)))



def high_adder(clips, **_):
    if len(clips) == 3:
        return core.llvmexpr.Expr(clips, """
xabs = abs($x - 32768)
yabs = abs($y - 32768)
zabs = abs($z - 32768)
xsign = $x >= 32768 ? 1 : -1
ysign = $y >= 32768 ? 1 : -1
zsign = $z >= 32768 ? 1 : -1
xpow = copysign(xabs ** 5, xsign)
ypow = copysign(yabs ** 5, ysign)
zpow = copysign(zabs ** 5, zsign)
sum = (xpow + ypow + zpow) * (2 / 3)
sumabs = abs(sum)
sumsign = sum >= 0 ? 1 : -1
RESULT = copysign(sumabs ** 0.2, sumsign) + 32768
""", infix=1)
    else:
        assert len(clips) == 2
        return core.llvmexpr.Expr(clips, """
xabs = abs($x - 32768)
yabs = abs($y - 32768)
xsign = $x >= 32768 ? 1 : -1
ysign = $y >= 32768 ? 1 : -1
RESULT = 0
if (xsign == ysign) {
  RESULT = xabs ** 5 + yabs ** 5
} else {
  RESULT = abs(xabs ** 5 - yabs ** 5)
}
RESULT = RESULT ** 0.2
if (xabs >= yabs) {
  RESULT = copysign(RESULT, xsign) + 32768
} else {
  RESULT = copysign(RESULT, ysign) + 32768
}
""", infix=1)
def low_filter(clips, **_):
    merge = MeanMode.ARITHMETIC(clips)


    dn = DFTTest().denoise(merge, {0.0:0.06, 0.5:0.12, 0.7:0.60, 1.0:1.00}, tr=1, planes=[0])

    dn_y = get_y(dn)
    aa_mask = FreyChen().edgemask(dn_y)
    aa_mask = aa_mask.akarin.Expr("x 5600 - 24 *")
    aa_mask = Morpho.inflate(aa_mask, iterations=1)

    aa = based_aa(dn, mask=aa_mask, rfactor=1.5)


    dh_mask = Morpho.maximum(aa_mask, iterations=2)
    
    dh = dehalo_alpha(aa, brightstr=0.45, highsens=25)
    dh = core.std.MaskedMerge(aa, dh, dh_mask, planes=[0])
    dh = core.akarin.Expr([dh, aa], ["x y - 45 + 0 min y +", ""])
    
    dh_final_ref = bilateral(aa, ref=dh, sigmaR=5 / 255, sigmaS=12, planes=[0])
    dh_final = core.akarin.Expr([aa, dh, dh_final_ref], ["y z < z x min y ?", ""])


    return dh_final
merge = frequency_merge(*src, lowpass=lambda clip: DFTTest().denoise(clip, 4.0), mode_low=low_filter, mode_high=high_adder)



if sources[episode].op:
    op_src = []
    op_src_2058 = []
    op_src_2059 = []
    for op_ep in sources:
        if sources[op_ep].op:
            op_ep_len = sources[op_ep].op[1] - sources[op_ep].op[0]
            for source in ["source_j", "source_d", "source_m"]:
                if hasattr(sources[op_ep], source) and getattr(sources[op_ep], source):
                    op_ep_src = initialize_clip(core.bs.VideoSource(getattr(sources[op_ep], source)))
                    if len(op_src) < 16:
                        op_src.append(op_ep_src[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])
                    if op_ep_len >= 2158:
                        if len(op_src_2058) < 12:
                            op_src_2058.append(op_ep_src[sources[op_ep].op[0]+2158-1])
                    if op_ep_len >= 2159:
                        if len(op_src_2059) < 12:
                            op_src_2059.append(op_ep_src[sources[op_ep].op[0]+2159-1])

                if len(op_src_2059) >= 12:
                    break
        if len(op_src_2059) >= 12:
            break

    if episode != "01":
        print(f"\t\tfrequency_merge source check in progress", file=sys.stderr, end="\r")
        for fno, fr in enumerate(core.vszip.PlaneMinMax(core.akarin.Expr([src[0][sources[episode].op[0]:sources[episode].op[0]+2157], op_src[0]], ["x y - abs", ""]), prop="Luma")[::49].frames()):
            if fr.props["LumaMax"] > 72 << 8:
                print(f"\033[1;31m\t\tfrequency_merge source check error on frame {fno * 49} ({fno * 49 + sources[episode].op[0]})\033[0m", file=sys.stderr)
        else:
            print(f"\t\tfrequency_merge source check complete   ", file=sys.stderr)

    op_len = sources[episode].op[1] - sources[episode].op[0]
    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))
    merge = insert_clip(merge, op_merge, sources[episode].op[0])
    if op_len >= 2158:
        op_merge = frequency_merge(*op_src_2058, lowpass=lambda clip: DFTTest().denoise(clip))
        merge = insert_clip(merge, op_merge, sources[episode].op[0] + 2158 - 1)
    if op_len >= 2159:
        op_merge = frequency_merge(*op_src_2059, lowpass=lambda clip: DFTTest().denoise(clip))
        merge = insert_clip(merge, op_merge, sources[episode].op[0] + 2159 - 1)



db = pfdeband(merge, thr=1.7, debander=placebo_deband)

final = finalize_clip(db, dither_type=DitherType.NONE)



if "__main__" in dir(__main__):
    Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")

    output = SPath("Video") / f"{episode}.ivf"
    fgs_table = SPath("grain.tbl")

    settings = settings_builder_5fish_svt_av1_psy(preset=2,
                                                  crf=19.60,
                                                  lineart_psy_bias=3,
                                                  texture_psy_bias=6,
                                                  psy_bias_optimize_b=1,
                                                  fgs_table=str(fgs_table))
    SVTAV1(**settings, sd_clip=src_sd).encode(final, outfile=output)
else:
    final.set_output()
