function mux
    set_color -o white ; echo "[mux] Muxing..." ; set_color normal

    set -g mkv_command mkvmerge --deterministic 0

    set title "☆ Kimi wo Tsumugu ☆ Anime PV [Himejoshi]"
    set -g -a mkv_command --title $title

    set output_file "Publish/[Himejoshi] Kimi wo Tsumugu - Anime PV (WEB 1080p AV1).mkv"
    set -g -a mkv_command --output $output_file

    set video_file "Video/encode.ivf"
    set -g -a mkv_command --language 0:ja --track-name 0:"Himejoshi" $video_file

    set audio_file "Sources/251.webm"
    set -g -a mkv_command --language 0:ja --track-name 0:"Himejoshi" $audio_file

    set subtitle_file "Subtitles/en.ass"
    set -g -a mkv_command --language 0:en --track-name 0:"Himejoshi" $subtitle_file

    set subtitle_file "Subtitles/de.ass"
    set -g -a mkv_command --language 0:de --track-name 0:"Himejoshi" $subtitle_file

    set -g -a mkv_command --attach-file "Subtitles/SNPro-SemiBold.ttf"

    echo $mkv_command
    $mkv_command
    or return $status
    if not test -e $output_file
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end

    set output_torrent_file "Publish/[Himejoshi] Kimi wo Tsumugu - Anime PV (WEB 1080p AV1).mkv.torrent"
    mktorrent -vf -a http://nyaa.tracker.wf:7777/announce -a https://tracker.nekobt.to/api/tracker/public/announce -a udp://tracker.opentrackr.org:1337/announce -a udp://open.stealth.si:80/announce -a udp://tracker.torrent.eu.org:451/announce -a udp://exodus.desync.com:6969/announce -a https://tracker.anibt.net/announce -a http://t.acg.rip:6699/announce -o $output_torrent_file $output_file
    or return $status
    if not test -e $output_torrent_file
        set_color red ; echo "[mux] Output torrent file missing. Exiting..." ; set_color normal
        return 126
    end
end
