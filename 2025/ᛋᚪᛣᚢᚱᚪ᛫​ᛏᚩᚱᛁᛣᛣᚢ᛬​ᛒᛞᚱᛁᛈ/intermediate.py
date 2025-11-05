from muxtools import PathLike, VideoFile, make_output
from muxtools.utils.dataclass import allow_extra, dataclass
from vsmuxtools import VideoEncoder, x264
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


def encode_intermediate(episode, filterchain_results):
    outfile = SPath("Intermediate") / f"{episode}.mkv"
    return LosslessX264Mod().encode(filterchain_results.final, outfile=outfile)
