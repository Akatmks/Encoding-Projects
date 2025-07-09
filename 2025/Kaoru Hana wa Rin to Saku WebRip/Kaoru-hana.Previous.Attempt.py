from vsdehalo import fine_dehalo, edge_cleaner
from vsdenoise import DFTTest, frequency_merge
from privatevsfunc import private_aa
from vsmasktools import FreyChen, Morpho, Robinson3
import os
import vsTAAmbk
from vstools import core, depth, get_y, initialize_clip, join, SPath
from vodesfunc import schizo_denoise


source_file_avc = SPath(os.environ["SOURCE_FILE_AVC"])
if not source_file_avc.exists():
    raise FileNotFoundError("Source AVC file not found.")
source_file_av1 = SPath(os.environ["SOURCE_FILE_AV1"])
if not source_file_av1.exists():
    raise FileNotFoundError("Source AV1 file not found.")

src_avc = core.lsmas.LWLibavSource(source_file_avc)
src_avc = initialize_clip(src_avc)
src_av1 = core.lsmas.LWLibavSource(source_file_av1)
src_av1 = initialize_clip(src_av1)


# ---------------------------------------------------------------------
# Set the port used by the dispatch server. You can set it to any port
# of your preference, as long as you set it the same in `Server.py`,
# `Server-Shutdown.py` and your filtering vpy script.
port = 18861
# ---------------------------------------------------------------------
# Copy every line in this file to your filtering vpy script. The
# optimal place to paste this is after you've imported vapoursynth and
# all the vsfunc's, and after you've loaded the source file, but before
# any filtering using VRAM is created / performed.
# ---------------------------------------------------------------------


dn_avc = schizo_denoise(src_avc, radius=3)

dn_avc_y = get_y(dn_avc)
aa_avc_y = vsTAAmbk.TAAmbk(dn_avc_y, aatype="Eedi2", strength=0.5, cuda=True)

mask = Robinson3().edgemask(dn_avc_y)
mask = Morpho.closing(mask)
mask = Morpho.maximum(mask, iterations=2)
aa_avc_y = core.akarin.Expr([aa_avc_y, dn_avc_y, mask], "z 13000 > x y ?")
aa_avc = join(aa_avc_y, dn_avc)


merge = frequency_merge(src_av1, aa_avc, mode_high=aa_avc, mode_low=src_av1,
                        lowpass=DFTTest(slocation=[0.00,50.0, 0.55,50.0, 0.60,0.1, 1.00,0.1], tbsize=1).denoise)


merge_y = get_y(merge)
aa_y = private_aa(merge_y, strength=0.88)
aa = join(aa_y, merge)

aadh = edge_cleaner(aa, strength=12)

mask = Robinson3().edgemask(merge_y)
mask = Morpho.closing(mask)
mask = Morpho.maximum(mask, iterations=2)
mask = Morpho.inflate(mask)
aadh_y = core.akarin.Expr([get_y(aadh), merge_y, mask], "z 13000 > x y ?")
aadh = join(aadh_y, merge)

dh_final = fine_dehalo(aadh, brightstr=0.9, rx=2.0, ry=2.0, edgemask=FreyChen(), edgeproc=1.0, exclude=False)


out = depth(dh_final, 10)
out.set_output()
