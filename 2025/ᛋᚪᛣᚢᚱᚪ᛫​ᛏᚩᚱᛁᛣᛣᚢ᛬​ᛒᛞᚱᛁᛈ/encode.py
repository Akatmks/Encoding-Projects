from muxtools import make_output, PathLike, VideoFile
from muxtools.utils.dataclass import allow_extra, dataclass
from vsmuxtools import settings_builder_x265, VideoEncoder, x264, x265
import shlex
from vstools import SPath, vs


@dataclass(config=allow_extra)
class LosslessX264Mod(VideoEncoder):
    add_props: bool = True

    def encode(self, clip: vs.VideoNode, outfile: PathLike | None = None) -> VideoFile:
        out = make_output("lossless", "mkv", user_passed=outfile)
        settings = ["--output-depth", "10", "--preset", "slow", "--qp", "0"] + self.get_custom_args() + ["--colorprim", "bt709", "--transfer", "bt709", "--colormatrix", "bt709"]

        assert clip.format.bits_per_sample == 10

        avc = x264(shlex.join(settings), add_props=self.add_props, resumable=False)
        avc._update_settings(clip, False)
        avc._encode_clip(clip, out, None, 0)
        return VideoFile(out)

def intermediate(episode, final):
    output = SPath("Intermediate") / f"{episode}.mkv"
    return LosslessX264Mod().encode(final, outfile=output)


def main(episode, final):
    output = SPath("Main") / f"{episode}.265"

    settings = settings_builder_x265(hist_scenecut="", frames=final.num_frames,
                                     crf=13.50, qcomp=0.80, aq_strength=0.66, chroma_qpoffsets=-3)
    return x265(settings, resumable=False, csv=SPath("Temp") / f"{episode}.x265_log.csv").encode(final, outfile=output)
