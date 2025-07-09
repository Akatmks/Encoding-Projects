import os
from vstools import core


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
source_lwi_file = SPath(os.environ["SOURCE_LWI_FILE"])


src = core.lsmas.LWLibavSource(source_file, cachefile=source_lwi_file)
src.set_output()
