from dataclasses import dataclass
import os
from vstools import FrameRangeN, SPath


assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])


@dataclass
class Source:
    source_e: SPath | None = None
    source_y: SPath | None = None
    source_2: SPath | None = None
    op: FrameRangeN | None = None


sources = {
    "01": Source(op=(6162, 8320)), # 2158
    "02": Source(op=(816, 2973)),
    "03": Source(op=(864, 3021)),
    "04": Source(op=(2254, 4411)),
    "05": Source(op=(1080, 3237)),
    "06": Source(op=(1176, 3333)),
    "07": Source(op=(0, 2158)), # 2158
    "08": Source(op=(4891, 7050)), # 2159
    "09": Source(op=(3909, 6066)),
    "10": Source(op=(1392, 3549)),
    "11": Source(op=(3693, 5850)),
    "12": Source(op=(360, 2518)) # 2158
}

for episode in sources:
    matches = list(raws.glob(f"[E* - {episode} *"))
    assert(len(matches) == 1)
    sources[episode].source_e = matches[0]

    matches = list(raws.glob(f"[Y* - S01E{episode} *"))
    if matches:
        assert(len(matches) == 1)
        sources[episode].source_y = matches[0]

    matches = list(raws.glob(f"[S* - {episode}v2 *"))
    if matches:
        assert(len(matches) == 1)
        sources[episode].source_2 = matches[0]
