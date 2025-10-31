from dataclasses import dataclass, field
from muxtools import Trim
import os
from vstools import FrameRangeN, FrameRangesN, SPath
from typing import Literal


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
    ed_type: Literal[1, 2] | None = None
    title_cards: FrameRangesN = field(default_factory=list) # Exclusive
    preview_cards: FrameRangesN = field(default_factory=list) # Exclusive


sources = {
    "01": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(3813, 5966), ed=(31909, 34067), ed_type=1,
                 title_cards=[(6747, 6831), (19525, 19585), (20618, 20702), (31849, 31909), (34586, 34783)],
                 preview_cards=[(34161, 34586)]),
    "02": Source(source=vol_01_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(0, 2154), ed=(31883, 34041), ed_type=1,
                 title_cards=[(2663, 2747), (16239, 16299), (17435, 17519), (31823, 31883), (34557, 34757)],
                 preview_cards=[(34095, 34557)]),
    "03": Source(source=vol_02_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(24, 2178), ed=(31908, 34066), ed_type=1,
                 title_cards=[(3067, 3151), (20000, 20147), (31848, 31908), (34558, 34782)],
                 preview_cards=[(34141, 34558)]),
    "04": Source(source=vol_02_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(1224, 3377), ed=(31885, 34043), ed_type=1,
                 title_cards=[(3377, 3461), (18613, 18673), (18814, 18898), (31825, 31885), (34562, 34759)],
                 preview_cards=[(34097, 34562)]), # film_grain_scenes=[(26508, 26593)] # Just tank it
    "05": Source(source=vol_03_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(24, 2178), ed=(31907, 34065), ed_type=1,
                 title_cards=[(3543, 3627), (15783, 15843), (16653, 16737), (31037, 31193), (31847, 31907), (34574, 34781)],
                 preview_cards=[(34095, 34574)]),
    "06": Source(source=vol_03_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(0, 2154), ed=(31883, 34041), ed_type=1,
                 title_cards=[(3332, 3416), (16767, 16827), (17169, 17253), (31823, 31883), (34521, 34757)],
                 preview_cards=[(34071, 34521)]),
    "07": Source(source=vol_04_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(2710, 4863), ed=(31909, 34067), ed_type=1,
                 title_cards=[(6786, 6870), (20172, 20232), (20912, 20996), (30805, 30913), (31849, 31909), (34577, 34783)],
                 preview_cards=[(34097, 34577)]),
    "08": Source(source=vol_04_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(2422, 4575), ed=(31883, 34041), ed_type=2,
                 title_cards=[(6020, 6104), (16648, 16708), (18291, 18375), (31823, 31883), (34545, 34757)],
                 preview_cards=[(34068, 34545)]),
    "09": Source(source=vol_05_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(24, 2178), ed=(31907, 34065), ed_type=1,
                 title_cards=[(4672, 4756), (15999, 16059), (16929, 17013), (24245, 24389), (31847, 31907), (34587, 34781)],
                 preview_cards=[(34098, 34587)]),
    "10": Source(source=vol_05_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(0, 2154), ed=(31884, 34042), ed_type=1,
                 title_cards=[(2604, 2688), (14537, 14597), (16135, 16219), (30242, 30386), (31824, 31884), (34607, 34758)],
                 preview_cards=[(34069, 34607)]),
    "11": Source(source=vol_06_bdmv / "BDMV" / "STREAM" / "00001.m2ts",
                 op=(24, 2178), ed=(31908, 34066), ed_type=1,
                 title_cards=[(2995, 3079), (17462, 17522), (19612, 19696), (31848, 31908), (34650, 34782)],
                 preview_cards=[(34099, 34650)]),
    "12": Source(source=vol_06_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(576, 2730), ed=(31886, 34044), ed_type=1,
                 title_cards=[(3697, 3781), (14179, 14239), (15348, 15432), (31802, 31886)]),
    "NCOP": Source(source=vol_02_bdmv / "BDMV" / "STREAM" / "00010.m2ts",
                   trim=(None, -24)),
    "NCED01": Source(source=vol_03_bdmv / "BDMV" / "STREAM" / "00010.m2ts",
                     trim=(24, -24)),
    "NCED02": Source(source=vol_04_bdmv / "BDMV" / "STREAM" / "00010.m2ts",
                     trim=(None, -26))
}
