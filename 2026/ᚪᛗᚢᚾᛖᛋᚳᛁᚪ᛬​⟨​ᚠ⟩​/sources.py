from dataclasses import dataclass, field
import os
from vstools import FrameRangeN, FrameRangesN, SPath


assert "VOL_01_BDMV_DIRECTORY" in os.environ
vol_01 = SPath(os.environ["VOL_01_BDMV_DIRECTORY"])
assert "VOL_02_BDMV_DIRECTORY" in os.environ
vol_02 = SPath(os.environ["VOL_02_BDMV_DIRECTORY"])
assert "VOL_03_BDMV_DIRECTORY" in os.environ
vol_03 = SPath(os.environ["VOL_03_BDMV_DIRECTORY"])
assert "VOL_04_BDMV_DIRECTORY" in os.environ
vol_04 = SPath(os.environ["VOL_04_BDMV_DIRECTORY"])
assert "VOL_05_BDMV_DIRECTORY" in os.environ
vol_05 = SPath(os.environ["VOL_05_BDMV_DIRECTORY"])
assert "VOL_06_BDMV_DIRECTORY" in os.environ
vol_06 = SPath(os.environ["VOL_06_BDMV_DIRECTORY"])


@dataclass
class Source:
    source: SPath | None = None
    op: FrameRangeN | None = None
    op_offset: int = 0
    ed: FrameRangeN | None = None
    credits: FrameRangesN = field(default_factory=list)


sources = {
    "01": Source(source=vol_01 / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(24, 2183),
                 credits=[(31855, None)]),
    "02": Source(source=vol_01 / "BDMV" / "STREAM" / "00003.m2ts",
                 op=(0, 2159),
                 credits=[(30680, 32536), (33686, None)]),
    "03": Source(source=vol_02 / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(24, 2183),
                 credits=[(31855, None)]),
    "04": Source(source=vol_02 / "BDMV" / "STREAM" / "00003.m2ts",
                 op=(0, 2159),
                 credits=[(31830, None)]),
    "05": Source(source=vol_03 / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(24, 2183),
                 credits=[(31854, None)]),
    "06": Source(source=vol_03 / "BDMV" / "STREAM" / "00003.m2ts",
                 op=(0, 2159),
                 credits=[(31830, None)]),
    "07": Source(source=vol_04 / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(24, 2183),
                 credits=[(31853, None)]),
    "08": Source(source=vol_04 / "BDMV" / "STREAM" / "00003.m2ts",
                 op=(0, 2159),
                 credits=[(31831, None)]),
    "09": Source(source=vol_05 / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(24, 2183), op_offset=1,
                 credits=[(31855, None)]),
    "10": Source(source=vol_05 / "BDMV" / "STREAM" / "00003.m2ts",
                 op=(0, 2159),
                 credits=[(31831, None)]),
    "11": Source(source=vol_06 / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(24, 2183),
                 credits=[(31855, None)]),
    "12": Source(source=vol_06 / "BDMV" / "STREAM" / "00003.m2ts",
                 credits=[(31146, 33249)]),
}

for ep in sources:
    source = sources[ep]
    if source.op:
        source.credits.append((source.op[0], source.op[0] + 630))
        source.credits.append((source.op[0] + 867, source.op[1]))
