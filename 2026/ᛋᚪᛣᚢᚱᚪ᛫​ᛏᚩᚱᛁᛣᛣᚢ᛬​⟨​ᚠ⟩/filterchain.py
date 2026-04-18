import os
import sys
sys.path.insert(0, os.getcwd())

from vsaa import based_aa, EEDI3
from vsdeband import Grainer, placebo_deband
from vsdenoise import bm3d, decrease_size, DFTTest, mc_degrain, MotionMode, MVTools, Prefilter, SADMode, wnnm
from vsmasktools import diff_creditless, Morpho, RScharr
import vsmlrt
from vsmuxtools import SourceFilter, src_file
from vskernels import Lanczos
from vsrgtools import gauss_blur, remove_grain
from vsscale import Rescale
from vstools import core, depth, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, join, replace_ranges, Sar, SPath, split, vs

from sources import intermediates, sources



def intermediate_filterchain(episode):
    source_file = src_file(sources[episode].source, trim=sources[episode].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
    src = source_file.init_cut()

    if sources[episode].op is not None:
        op_file = src_file(sources["NCOP"].source, trim=sources["NCOP"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        op = op_file.init_cut()

    if sources[episode].ed is not None:
        assert sources[episode].ed_type in [1, 2]
        if sources[episode].ed_type == 1:
            ed_file = src_file(sources["NCED01"].source, trim=sources["NCED01"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        else:
            ed_file = src_file(sources["NCED02"].source, trim=sources["NCED02"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        ed = ed_file.init_cut()

    if len(sources[episode].preview_cards) > 0:
        preview_card_mask = core.bs.VideoSource(SPath(__file__) / ".." / "preview_card_mask.png", fpsnum=24000, fpsden=1001)
        preview_card_mask = depth(preview_card_mask, 16)
        preview_card_mask = preview_card_mask.std.Loop()



    rs = Rescale(src, width=1920*(1552-1)/(1920-1), height=1080*(873-1)/(1080-1), base_width=1552, base_height=873, kernel=Lanczos(2))


    descale = rs.descale
    cclip = src.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                               width=1552, height=873, src_width=1920+((1920-1)/(1552-1)-1), src_height=1080+((1080-1)/(873-1)-1), src_left=-((1920-1)/(1552-1)-1)/2, src_top=-((1080-1)/(873-1)-1)/2,
                               format=vs.YUV444P16)
    cclip = join(descale, cclip)
    cclip = cclip.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                                 width=1600, height=896, src_width=1600, src_height=896, src_left=-24, src_top=-11,
                                 format=vs.RGBS, range=1)
    cclip = cclip.akarin.Expr(["", "1.0 x - 0.75 * 1.0 swap -", "1.0 x - 0.9 * 1.0 swap -"])

    cclip = vsmlrt.inference(cclip, SPath(vsmlrt.models_path) / "anime-segmentation" / "isnet_is.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
    cclip = cclip.akarin.Expr("""
                     x[0,-2]
            x[-1,-1] x[0,-1] x[1,-1]
    x[-2,0] x[-1,0]  x[0,0]  x[1,0]  x[2,0]
            x[-1,1]  x[0,1]  x[1,1]
                     x[0,2]
    sort13 drop10 high! drop2
    high@ 0.90 > x 0.85 > and x x 9 pow ? continue!
    continue@ 0.15 > continue@ 0 ?
    """)
    cclip = cclip.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                                 width=3104, height=1746, src_width=1552, src_height=873, src_left=24, src_top=11)
    cclip = gauss_blur(cclip, sigma=1.6)
    cclip = Morpho.maximum(cclip, iterations=1)
    cclip = depth(cclip, 16, dither_type=DitherType.NONE)

    doubled = rs.doubled
    uniform_mask = core.akarin.Expr([doubled, cclip], "y x 0 ?")
    uniform_mask = uniform_mask.vszip.PlaneAverage(prop="Brightness", exclude=[0])
    uniform_mask = uniform_mask.akarin.PropExpr(dict=lambda: dict(BrightnessThr="x.BrightnessAvg 65535 *"))
    uniform_mask = uniform_mask.akarin.PropExpr(dict=lambda: dict(BrightnessMultipler="65535 x.BrightnessThr 4096 - 0.1 max 0.4 * /"))
    uniform_mask = uniform_mask.akarin.Expr("""x x.BrightnessThr x - x.BrightnessMultipler * 0 ?""")
    uniform_mask = Morpho.opening(uniform_mask, radius=5)
    uniform_mask = gauss_blur(uniform_mask, sigma=0.8)
    uniform_mask = Morpho.erosion(uniform_mask, radius=1)

    aa_mask = core.akarin.Expr([cclip, uniform_mask], "x y min")

    aa = based_aa(doubled, supersampler=False, antialiaser=EEDI3(alpha=0.4), mask_thr=25)
    aa_diff = core.akarin.Expr([aa, doubled], "x y - 32768 +")
    aa = core.akarin.Expr([aa_diff, doubled], """
    x 32768 - diff!
    diff@ 0 >
                 x[-3,-4] x[-2,-4] x[-1,-4] x[0,-4] x[1,-4] x[2,-4] x[3,-4]
        x[-4,-3] x[-3,-3] x[-2,-3] x[-1,-3] x[0,-3] x[1,-3] x[2,-3] x[3,-3] x[4,-3]
        x[-4,-2] x[-3,-2] x[-2,-2] x[-1,-2] x[0,-2] x[1,-2] x[2,-2] x[3,-2] x[4,-2]
        x[-4,-1] x[-3,-1] x[-2,-1] x[-1,-1] x[0,-1] x[1,-1] x[2,-1] x[3,-1] x[4,-1]
        x[-4,0]  x[-3,0]  x[-2,0]  x[-1,0]          x[1,0]  x[2,0]  x[3,0]  x[4,0]
        x[-4,1]  x[-3,1]  x[-2,1]  x[-1,1]  x[0,1]  x[1,1]  x[2,1]  x[3,1]  x[4,1]
        x[-4,2]  x[-3,2]  x[-2,2]  x[-1,2]  x[0,2]  x[1,2]  x[2,2]  x[3,2]  x[4,2]
        x[-4,3]  x[-3,3]  x[-2,3]  x[-1,3]  x[0,3]  x[1,3]  x[2,3]  x[3,3]  x[4,3]
                 x[-3,4]  x[-2,4]  x[-1,4]  x[0,4]  x[1,4]  x[2,4]  x[3,4]
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min darken!
        diff@ 32768 darken@ - min
        diff@ ?
    y +
    """)

    aa = core.std.MaskedMerge(doubled, aa, aa_mask)
    rs.doubled = aa


    descale_mask = src.std.BlankClip(format=vs.GRAY16)

    def process_oped_mask(oped_mask):
        oped_mask = remove_grain(oped_mask, mode=remove_grain.Mode.MINMAX_AROUND2)
        oped_mask = oped_mask.akarin.Expr("""
        x
                     x[-3,-4] x[-2,-4] x[-1,-4] x[0,-4] x[1,-4] x[2,-4] x[3,-4]
            x[-4,-3] x[-3,-3] x[-2,-3] x[-1,-3] x[0,-3] x[1,-3] x[2,-3] x[3,-3] x[4,-3]
            x[-4,-2] x[-3,-2] x[-2,-2] x[-1,-2] x[0,-2] x[1,-2] x[2,-2] x[3,-2] x[4,-2]
            x[-4,-1] x[-3,-1] x[-2,-1]                          x[2,-1] x[3,-1] x[4,-1]
            x[-4,0]  x[-3,0]  x[-2,0]                           x[2,0]  x[3,0]  x[4,0]
            x[-4,1]  x[-3,1]  x[-2,1]                           x[2,1]  x[3,1]  x[4,1]
            x[-4,2]  x[-3,2]  x[-2,2]  x[-1,2]  x[0,2]  x[1,2]  x[2,2]  x[3,2]  x[4,2]
            x[-4,3]  x[-3,3]  x[-2,3]  x[-1,3]  x[0,3]  x[1,3]  x[2,3]  x[3,3]  x[4,3]
                     x[-3,4]  x[-2,4]  x[-1,4]  x[0,4]  x[1,4]  x[2,4]  x[3,4]
            sort68 drop61 measure! drop6
            measure@ 0 ?
        """)
        oped_mask = Morpho.expand(oped_mask, sw=1)
        oped_mask = Morpho.inflate(oped_mask, radius=3, iterations=2)
        oped_mask = Morpho.closing(oped_mask, radius=3)
        return oped_mask

    if sources[episode].op is not None:
        op_mask = diff_creditless(src[sources[episode].op[0]+534:sources[episode].op[0]+609], op[534:609],
                                  thr=0.36, expand=-2, prefilter=True)
        op_mask = process_oped_mask(op_mask)
        descale_mask = insert_clip(descale_mask, op_mask, start_frame=sources[episode].op[0]+534)

    if sources[episode].ed is not None:
        assert sources[episode].ed[1] - sources[episode].ed[0] <= ed.num_frames

        if sources[episode].ed_type == 1:
            ed_mask = diff_creditless(src[sources[episode].ed[0]:sources[episode].ed[1]], ed,
                                      thr=0.18, expand=-2, prefilter=True)
        else:
            ed_mask = diff_creditless(src[sources[episode].ed[0]:sources[episode].ed[1]], ed,
                                      thr=0.36, expand=-2, prefilter=True)
        ed_mask = process_oped_mask(ed_mask)
        descale_mask = insert_clip(descale_mask, ed_mask, start_frame=sources[episode].ed[0])

    title_card_mask = descale_mask.std.BlankClip(format=vs.GRAY16, color=[65535])
    descale_mask = replace_ranges(descale_mask, title_card_mask, sources[episode].title_cards, exclusive=True)

    descale_mask = replace_ranges(descale_mask, preview_card_mask, sources[episode].preview_cards, exclusive=True)

    rs.credit_mask = descale_mask


    line_mask = RScharr().edgemask(src)
    line_mask = Morpho.maximum(line_mask, planes=[0])
    line_mask = remove_grain(line_mask, mode=remove_grain.Mode.SMART_RGC, planes=[1, 2])
    line_mask = line_mask.resize.Bilinear(width=1920, height=1080, format=vs.YUV444P16, range_in_s="full", range_s="full")
    line_mask = core.akarin.Expr(split(line_mask), """
    x cont!       cont@ 6400 > cont@ 2 * 0 ? cont! cont@ 17600 > cont@ 17600 - 6 * 17600 + cont@ ? xcont!
    y z max cont! cont@ 4800 > cont@ 2 * 0 ? cont! cont@ 14400 > cont@ 14400 - 6 * 14400 + cont@ ? yzcont!
    xcont@ yzcont@ 65535 min 0.8 * max
    """)
    line_mask = Morpho.inflate(line_mask, radius=1)

    rs.line_mask = line_mask


    ds = rs.upscale

    ds = Sar.from_clip(src).apply(ds)



    dn_cclip = cclip.resize.Bilinear(width=1920, height=1080, src_width=2*1920*(1552-1)/(1920-1), src_height=2*1080*(873-1)/(1080-1), src_left=(1552-1)/(1920-1)-1, src_top=(873-1)/(1080-1)-1)
    dn_cclip = Morpho.inflate(dn_cclip, radius=1)
    dn_cclip = dn_cclip.resize.Bilinear(width=240, height=135)
    dn_cclip = remove_grain(dn_cclip, mode=remove_grain.Mode.BINOMIAL_BLUR)
    dn_line_mask = line_mask.resize.Bicubic(filter_param_a=0.0, filter_param_b=0.0, width=240, height=135)
    dn_cclip = core.akarin.Expr([dn_cclip, dn_line_mask], """
    x 3.5 * 65535 min
        y 65535 / 3.5 * 0.65 max 1 min *
    65535 0.3 * max
    """)
    dn_cclip = dn_cclip.resize.Point(width=1920, height=1080)

    ref = mc_degrain(ds, prefilter=Prefilter.DFTTEST(sloc={0.0:0.4, 0.4:0.6, 0.6:5.0, 1.0:8.0}), refine=2, thsad=160, tr=1)
    dn = bm3d(ds, ref=ref, sigma=1.33, tr=0, refine=2, profile=bm3d.Profile.LOW_COMPLEXITY, planes=[0])
    dn = core.std.MaskedMerge(ds, dn, dn_cclip, planes=[0])
    dn = wnnm(dn, ref=ref, sigma=1.33, tr=1, planes=[1, 2])



    final = finalize_clip(dn, bits=16)
    return final



def cache_intermediate(episode):
    core.bs.VideoSource(intermediates[episode], showprogress=False)



def main_filterchain(episode):
    dn = core.bs.VideoSource(intermediates[episode], showprogress=False)
    dn = initialize_clip(dn)



    db = placebo_deband(dn, thr=2.0, radius=22)

    dn_y = get_y(dn)
    db_y = get_y(db)
    diff = core.akarin.Expr([db_y, dn_y], ["x y - 64 * 32768 +"])
    diff_dct = diff.dctf.DCTFilter(factors=[0.9375, 0.85, 0.5,  0.3,  0.3,  0.3,  0.4,  0.6,
                                            0.85,   0.98, 0.85, 0.75, 0.75, 0.75, 0.85, 0.95,
                                            0.5,    0.85, 0.95, 0.95, 0.95, 0.95, 1,    1,
                                            0.3,    0.75, 0.95, 1,    0.98, 1,    1,    1,
                                            0.3,    0.75, 0.95, 0.98, 0.95, 0.98, 1,    1,
                                            0.3,    0.75, 0.95, 1,    0.98, 1,    1,    1,
                                            0.4,    0.85, 1,    1,    1,    1,    1,    1,
                                            0.6,    0.95, 1,    1,    1,    1,    1,    1])
    db_dct = core.akarin.Expr([dn_y, diff_dct], ["y 30720 - 64 / x +"])

    db = join(db_dct, db)
    db = core.vszip.LimitFilter(db, dn, dark_thr=0.55, bright_thr=0.55, elast=1.6)



    rg = Grainer.SIMPLEX(db, strength=(2.2, 0.55), size=(4*(1552-1)/(1920-1), 4*(873-1)/(1080-1)),
                             luma_scaling=7.2, temporal=(0.50, 3), seed=274810)



    final = finalize_clip(rg)
    return final



def mini_filterchain(episode):
    dn = core.bs.VideoSource(intermediates[episode], showprogress=False)
    dn = src_sd = initialize_clip(dn)



    dn = decrease_size(dn, sigmaS=3)

    base_dn = DFTTest(backend=DFTTest.Backend.OLD).denoise(dn, {0.0:0.08, 0.4:0.12, 0.6:0.60, 1.0:1.00}, sbsize=32, sosize=24, tr=1)

    base_db = placebo_deband(base_dn, thr=2.2, radius=22)

    base_dn_y = get_y(base_dn)
    base_db_y = get_y(base_db)
    diff = core.akarin.Expr([base_db_y, base_dn_y], ["x y - 64 * 32768 +"])
    diff_dct = diff.dctf.DCTFilter(factors=[0.9375, 0.85, 0.5,  0.3,  0.3,  0.3,  0.4,  0.6,
                                            0.85,   0.98, 0.85, 0.75, 0.75, 0.75, 0.85, 0.95,
                                            0.5,    0.85, 0.95, 0.95, 0.95, 0.95, 1,    1,
                                            0.3,    0.75, 0.95, 1,    0.98, 1,    1,    1,
                                            0.3,    0.75, 0.95, 0.98, 0.95, 0.98, 1,    1,
                                            0.3,    0.75, 0.95, 1,    0.98, 1,    1,    1,
                                            0.4,    0.85, 1,    1,    1,    1,    1,    1,
                                            0.6,    0.95, 1,    1,    1,    1,    1,    1])
    base_db_dct = core.akarin.Expr([base_dn_y, diff_dct], ["y 30720 - 64 / x +"])

    base_db = join(base_db_dct, base_db)

    base = core.akarin.Expr([base_db, base_dn, dn], "x y - z +")

    mv = MVTools(dn, search_clip=Prefilter.DFTTEST)

    mv.analyze(tr=2, blksize=32, overlap=16, truemotion=MotionMode.COHERENCE, divide=2)
    mv.recalculate(thsad=50, blksize=8, overlap=4, dct=SADMode.ADAPTIVE_SATD_DCT, truemotion=MotionMode.COHERENCE)

    dg = mv.degrain(base_db, base, tr=2, thsad=50, thscd=(100, 2))



    final = finalize_clip(dg, dither_type=DitherType.NONE)
    return final, src_sd
