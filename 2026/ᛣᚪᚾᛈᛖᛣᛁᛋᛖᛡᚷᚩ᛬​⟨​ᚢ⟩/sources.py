from dataclasses import dataclass, field
from muxtools import Trim
import os
from vstools import FrameRangeN, FrameRangesN, SPath
from typing import Literal


assert "VOL_01_BDMV_DIR" in os.environ
assert "VOL_02_BDMV_DIR" in os.environ
assert "WEB_DL_DIR" in os.environ

vol_01_bdmv = SPath(os.environ["VOL_01_BDMV_DIR"])
vol_02_bdmv = SPath(os.environ["VOL_02_BDMV_DIR"])
web_dl = SPath(os.environ["WEB_DL_DIR"])

assert "INTERMEDIATE_DIR" in os.environ

intermediate_dir = SPath(os.environ["INTERMEDIATE_DIR"])


@dataclass
class Source:
    source_bd: SPath | None = None
    source_web: SPath | None = None
    op: FrameRangeN | None = None # Exclusive


sources = {
    "01": Source(op=None),
    "02": Source(),
    "03": Source(),
    "04": Source(),
    "05": Source(),
    "06": Source(),
    "07": Source(),
    "08": Source(),
    "09": Source(),
    "10": Source(),
    "11": Source(),
    "12": Source(),
    "NCOP": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00006.m2ts"),
    "NCED01": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00007.m2ts"),
    "NCED02": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00006.m2ts"),
    "NCED03": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00007.m2ts"),
    "NCED04": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00008.m2ts")
}

for episode in range(1, 7):
    sources[f"{episode:02}"].source_bd = vol_01_bdmv / "BDMV" / "STREAM" / f"{episode - 1:05}.m2ts"
    assert sources[f"{episode:02}"].source_bd.exists()
for episode in range(7, 13):
    sources[f"{episode:02}"].source_bd = vol_01_bdmv / "BDMV" / "STREAM" / f"{episode - 7:05}.m2ts"
    assert sources[f"{episode:02}"].source_bd.exists()

for episode in range(1, 13):
    matches = list(web_dl.glob(f"T*.S01E{episode:02}.*b.mkv"))
    assert(len(matches) == 1)
    sources[f"{episode:02}"].source_web = matches[0]
