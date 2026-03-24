from dataclasses import dataclass
import os
from vstools import FrameRangeN, FrameRangesN, SPath


assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])


@dataclass
class Source:
    source: SPath | None = None
    source_s: SPath | None = None
    op: FrameRangeN | None = None
    ed: FrameRangeN | None = None
    outro: FrameRangeN | None = None


sources = {
    "01": Source(op=(4269, 6426), # Every episode 2157
                 ed=(30761, 32918),
                 outro=(32918, 33686)),
    "02": Source(op=(2830, 4987),
                 ed=(31527, 33685)),
    "03": Source(op=(2734, 4891),
                 ed=(31527, 33685)),
    "04": Source(op=(3285, 5443), # 2158!
                 ed=(31527, 33685)),
    "05": Source(op=(1894, 4053), # 2159!
                 ed=(31528, 33686)),
    "06": Source(op=(864, 3021),
                 ed=(31529, 33687)),
    "07": Source(op=(2422, 4579),
                 ed=(31528, 33686)),
    "08": Source(op=(1942, 4101), # 2159!
                 ed=(31530, 33688)),
    "09": Source(op=(1296, 3453),
                 ed=(31529, 33687)),
    "10": Source(op=(1534, 3693), # 2159!
                 ed=(31528, 33686)),
    "11": Source(op=(576, 2734), # 2158
                 ed=(31530, 33688)),
    "12": Source(op=(2182, 4339),
                 ed=(31528, 33686)),
    "13": Source(op=(1774, 3933),
                 ed=(27236, 29394),
                 outro=(29394, None))
}

for episode in sources:
    matches = list(raws.glob(f"[E* - {episode} *"))
    assert(len(matches) == 1)
    sources[episode].source = matches[0]

for episode in sources:
    matches = list(raws.glob(f"[S* - {episode} *"))
    assert(len(matches) == 1)
    sources[episode].source_s = matches[0]
