from dataclasses import dataclass, field
import os
from vstools import FrameRangeN, FrameRangesN, SPath


assert "OVA_BMDV_DIRECTORY" in os.environ
ova = SPath(os.environ["OVA_BMDV_DIRECTORY"])


@dataclass
class OVASource:
    source: SPath | None = None
    op: FrameRangeN | None = None


ova_source = OVASource(source=ova / "BDMV" / "STREAM" / "00001.m2ts",
                       op=[24, 2183])
