from vsaa import based_aa, EEDI3
from dataclasses import dataclass
from vsmasktools import diff_creditless, Morpho
import vsmlrt
from vsmuxtools import SourceFilter, src_file
from vskernels import Bilinear, Lanczos
from vsrgtools import gauss_blur, remove_grain
from vsscale import Rescale, Waifu2x
from vstools import depth, DitherType, insert_clip, SPath, vs

from .sources import Source, sources

@dataclass
class FilterchainResult:
    final: vs.VideoNode
    audio: src_file

def filterchain(episode: str) -> FilterchainResult:
    source_file = src_file(sources[episode].source, trim=sources[episode].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
    src = source_file.init_cut()

    if sources[episode].op is not None:
        op_file = src_file(sources["NCOP"].source, trim=sources["NCOP"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        op = op_file.init_cut()

    if sources[episode].ed is not None:
        ed_file = src_file(sources["NCED"].source, trim=sources["NCED"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        ed = ed_file.init_cut()



    rs = Rescale(src, width=1920*(1552-1)/(1920-1), height=1080*(873-1)/(1080-1), base_width=1552, base_height=873, kernel=Lanczos(2), downscaler=Bilinear(linear=True))


    descale = rs.descale
    rs.descale = descale    
    cclip = src.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                               width=1552, height=873, src_width=1920+((1920-1)/(1552-1)-1), src_height=1080+((1080-1)/(873-1)-1), src_left=-((1920-1)/(1552-1)-1)/2, src_top=-((1080-1)/(873-1)-1)/2,
                               format=vs.YUV444P16)
    cclip = join(descale, cclip)
    cclip = cclip.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                                 width=1600, height=896, src_width=1600, src_height=896, src_left=-24, src_top=-11,
                                 format=vs.RGBS, range=1)
    
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
    uniform_mask = doubled.std.PlaneStats(prop="Brightness")
    uniform_mask = uniform_mask.akarin.PropExpr(dict=lambda: dict(BrightnessThr="x.BrightnessAverage 65535 *"))
    uniform_mask = uniform_mask.akarin.PropExpr(dict=lambda: dict(BrightnessMultipler="65535 x.BrightnessThr 4096 - 0.1 max 0.51 * /"))
    uniform_mask = uniform_mask.akarin.Expr("""x.BrightnessThr x - x.BrightnessMultipler *""")
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

        ed_mask = diff_creditless(src[sources[episode].ed[0]:sources[episode].ed[1]], ed,
                                  thr=0.18, expand=-2, prefilter=True)

        ed_mask = process_oped_mask(ed_mask)
        
        descale_mask = insert_clip(descale_mask, ed_mask, start_frame=sources[episode].ed[0])

    # XXX title card mask

    rs.credit_mask = descale_mask


    ds = rs.upscale
