from dataclasses import dataclass
from muxtools import Trim
import os
from vstools import FrameRangeN, FrameRangesN, SPath


assert "VOL_01_BDMV_DIR" in os.environ
assert "VOL_02_BDMV_DIR" in os.environ
assert "VOL_03_BDMV_DIR" in os.environ
assert "VOL_04_BDMV_DIR" in os.environ
assert "VOL_05_BDMV_DIR" in os.environ
assert "VOL_06_BDMV_DIR" in os.environ

vol_01_bdmv = SPath(os.environ["VOL_01_BDMV_DIR"])
vol_02_bdmv = SPath(os.environ["VOL_02_BDMV_DIR"])
vol_03_bdmv = SPath(os.environ["VOL_03_BDMV_DIR"])
vol_04_bdmv = SPath(os.environ["VOL_04_BDMV_DIR"])
vol_05_bdmv = SPath(os.environ["VOL_05_BDMV_DIR"])
vol_06_bdmv = SPath(os.environ["VOL_06_BDMV_DIR"])


@dataclass
class Source:
    source: SPath
    trim: Trim = (None, None)
    op: FrameRangeN = None # Exclusive
    ed: FrameRangeN = None # Exclusive
    fullscreen_title_cards: FrameRangesN = [] # Exclusive
    title_cards: FrameRangesN = [] # Exclusive


sources = {
    "01": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(3813, 5966), ed=(31909, 34067)
                 title_cards=[(6747, 6831), (19525, 19585), (20618, 20702), (31849, 31909)]),
    "02": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(0, 2154), ed=(31883, 34041)
                 title_cards=[(2663, 2747), (16239, 16299), (17435, 17519), (31823, 31883)]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(, ), ed=(, )
                 title_cards=[]),
    "NCOP": Source(source=vol_02_bdmv / "BDMV" / "STREAM" / "00010.m2ts",
                   trim=(None, -24)),
    "NCED": Source(source=vol_03_bdmv / "BDMV" / "STREAM" / "00010.m2ts",
                   trim=(24, -24))
}
