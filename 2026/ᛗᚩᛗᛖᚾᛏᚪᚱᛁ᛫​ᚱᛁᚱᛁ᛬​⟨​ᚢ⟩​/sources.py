from dataclasses import dataclass
import os
from vstools import SPath

assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])

@dataclass
class Source:
    source: SPath
    source_sub: SPath

sources = {}

for episode in range(1, 15):
    source = list(raws.glob(f"[S* [{episode:02}*v"))
    assert(len(source) == 1)
    source_sub = list(raws.glob(f"[S* [{episode:02}*s"))
    assert(len(source_sub) == 1)
    sources[f"{episode:02}"] = Source(source=source[0], source_sub=source_sub[0])
