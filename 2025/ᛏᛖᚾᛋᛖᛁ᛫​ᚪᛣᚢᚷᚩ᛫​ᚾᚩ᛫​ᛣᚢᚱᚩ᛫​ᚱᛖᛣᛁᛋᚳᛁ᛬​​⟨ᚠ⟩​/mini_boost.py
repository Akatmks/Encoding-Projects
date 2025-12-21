import os
from vstools import core, SPath


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
source_ffindex_file = SPath(os.environ["SOURCE_FFINDEX_FILE"])


src = core.ffms2.Source(source_file, cachefile=source_ffindex_file)
src.set_output()
