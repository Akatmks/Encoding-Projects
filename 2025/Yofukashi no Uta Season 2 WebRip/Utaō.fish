#!/usr/bin/env fish

# $argv[1]: Input file
function extract
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[extract] Source file not found." ; set_color normal
        return 126
    end

    set --erase group
    set --erase episode

    set group (string match --regex --groups-only "Call\\.of\\.the\\.Night\\.S02E(\\d+).*REPACK\\..*NF.*VARYG" $source_file)
    if test -n "$group"
        set episode $group
        set group "VARYG REPACK"
    end
    if test -z "$group"
        set group (string match --regex --groups-only "Call\\.of\\.the\\.Night\\.S02E(\\d+).*NF.*VARYG" $source_file)
        if test -n "$group"
            set episode $group
            set group "VARYG NONREPACK"
        end
    end
    if test -z "$group"
        set group (string match --regex --groups-only "^\[(.*?)\]" (path basename $source_file))
    end
    if test -z "$group"
        set_color red ; echo "[extract] Unable to match group from filename..." ; set_color normal
        return 126
    end

    if test -z "$episode"
        set episode (string match --regex --groups-only "Call of the Night Season 2 - (\\d+)" $source_file)
    end
    if test -z "$episode"
        set episode (string match --regex --groups-only "Yofukashi no Uta Season 2 - (\\d+)" $source_file)
    end
    if test -z "$episode"
        set episode (string match --regex --groups-only "Yofukashi no Uta - S02E(\\d+)" $source_file)
    end
    if test -z "$episode"
        set_color red ; echo "[extract] Unable to match episode number from filename..." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[extract] Extracting subtitles for Yofukashi no Uta Season 2 Episode $episode..." ; set_color normal

    if test $group = "DantalianSubs"
        mkvextract $source_file tracks 2:"Subtitles/A [$group] $episode.es-419.ass"
    else if test $group = "Commie"
        mkvextract $source_file tracks 2:"Subtitles/B [$group] $episode.en.ass"
        mkvextract $source_file chapters "Chapters/$episode.xml"
        string replace --regex "00:00:00\\.033000000" "00:00:00.000000000" (cat "Chapters/$episode.xml") > "Chapters/$episode.xml"
    else if test $group = "VARYG REPACK"
        mkvextract $source_file tracks 4:"Subtitles/C [VARYG ADN] $episode.de.ass"
        mkvextract $source_file tracks 5:"Subtitles/C [VARYG ADN] $episode.fr.ass"
        mkvextract $source_file tracks 6:"Subtitles/D [VARYG NF] $episode.id.srt"
        mkvextract $source_file tracks 7:"Subtitles/D [VARYG NF] $episode.ms.srt"
        mkvextract $source_file tracks 8:"Subtitles/D [VARYG NF] $episode.th.srt"
        mkvextract $source_file tracks 9:"Subtitles/D [VARYG NF] $episode.vi.srt"
        mkvextract $source_file tracks 10:"Subtitles/D [VARYG NF] $episode.zh-Hant.srt"
    else if test $group = "VARYG NONREPACK"
        mkvextract $source_file tracks 3:"Subtitles/D [VARYG NF] $episode.id.srt"
        mkvextract $source_file tracks 4:"Subtitles/D [VARYG NF] $episode.ms.srt"
        mkvextract $source_file tracks 5:"Subtitles/D [VARYG NF] $episode.th.srt"
        mkvextract $source_file tracks 6:"Subtitles/D [VARYG NF] $episode.vi.srt"
        mkvextract $source_file tracks 7:"Subtitles/D [VARYG NF] $episode.zh-Hant.srt"
    else if test $group = "Erai-raws"
        mkvextract $source_file tracks 3:"Subtitles/C [Erai-raws ADN] $episode.fr.ass"
        mkvextract $source_file tracks 4:"Subtitles/C [Erai-raws ADN] $episode.de.ass"
    else
        set_color red ; echo "[extract] Unrecognised group [$group]..." ; set_color normal
        return 126
    end

    set fonts_dir "Subtitles/$episode.Fonts"
    if not test -e $fonts_dir
        mkdir $fonts_dir
    end
    begin cd $fonts_dir
        ffmpeg -hide_banner -y -dump_attachment:t "" -i $source_file
        prevd
    end

    if test $group = "VARYG REPACK"
        set_color -o white ; echo "[extract] Extracting audio for Yofukashi no Uta Season 2 Episode $episode..." ; set_color normal

        set audio_file "Audio/$episode.aac"
        mkvextract $source_file tracks 1:$audio_file
    else if test $group = "Erai-raws"
        set_color -o white ; echo "[extract] Extracting audio for Yofukashi no Uta Season 2 Episode $episode..." ; set_color normal

        set audio_file "Audio/$episode.aac"
        mkvextract $source_file tracks 1:$audio_file

        set audio_sync_file "Audio/$episode.aac.sync"
        echo "1001" > $audio_sync_file
    end

    set delay_warning (string match --regex ".*Delay.*" (MediaInfo $source_file))
    if test -n "$delay_warning"
        set_color -o red
        echo "[extract] Delay detected in the source:"
        echo $delay_warning
        set_color normal
    end
end

# $argv[1]: Input file
function boost
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[boost] Source file not found." ; set_color normal
        return 126
    end
    set episode (string match --regex --groups-only "Call\\.of\\.the\\.Night\\.S02E(\\d+).*NF.*VARYG" $source_file)
    if test -z "$episode"
        set_color red ; echo "[boost] Unable to match episode number from filename..." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[boost] Preparing Yofukashi no Uta Season 2 Episode $episode..." ; set_color normal

    set temp_dir_boost "Temp/$episode.boost.tmp"
    set scenes_file "Temp/$episode.scenes.json"
    set roi_maps_dir "Temp/$episode.roi.maps"
    python Progression-Boost.py --temp $temp_dir_boost --resume --input $source_file --output-scenes $scenes_file --output-roi-maps $roi_maps_dir
    or return $status
    if not test -e $scenes_file
        set_color red ; echo "[boost] Generated scenes file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Input file
# $argv[2]: CPU Usage "80" (Default)
function encode
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[encode] Source file not found." ; set_color normal
        return 126
    end
    set episode (string match --regex --groups-only "Call\\.of\\.the\\.Night\\.S02E(\\d+).*NF.*VARYG" $source_file)
    if test -z "$episode"
        set_color red ; echo "[encode] Unable to match episode number from filename..." ; set_color normal
        return 126
    end

    set usage $argv[2]
    if test -z $usage
        set usage 80
    end

    set scenes_file "Temp/$episode.scenes.json"
    if begin test -z $scenes_file ; or not test -e $scenes_file ; end
        set_color red ; echo "[encode] Scenes file not found." ; set_color normal
        return 126
    end
    set roi_maps_dir "Temp/$episode.roi.maps"
    if begin test -z $roi_maps_dir ; or not test -e $roi_maps_dir ; end
        set_color red ; echo "[encode] ROI map directory not exists." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding Yofukashi no Uta Season 2 Episode $episode..." ; set_color normal

    set_color -o magenta ; echo "[encode] Starting dispatch server..." ; set_color normal
    USAGE=$usage python Server.py &
    
    set video_file "Video/$episode.mkv"
    if test -e $video_file
        set_color -o yellow ; echo "[encode] Target video file already exists. Continuing..." ; set_color normal
    end
    set temp_dir "Temp/$episode.tmp"
    if test -e $temp_dir
        set_color -o yellow ; echo "[encode] Temp dir already exists. Continuing..." ; set_color normal
    end
    SOURCE_FILE=$source_file av1an -y --max-tries 5 --temp $temp_dir --resume --keep --verbose --log-level debug -i Utaō.py -o $video_file --scenes $scenes_file --chunk-order random --chunk-method lsmash --workers 6 --encoder svt-av1 --no-defaults --video-params "[1;5m:hanasaku:[0m" --pix-format yuv420p10le --concat mkvmerge
    or begin set status_ $status
        python Server-Shutdown.py
        set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal
        return $status_
    end

    python Server-Shutdown.py
    or return $status
    set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal

    if not test -e $video_file
        set_color red ; echo "[encode] Encoded video file missing. Exiting..." ; set_color normal
        return 126
    end
end

function shutdown
    python Server-Shutdown.py
    or return $status
end

# $argv[1]: Episode number "01"
function mux
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux] Episode number not provided." ; set_color normal
        return 126
    end

    set mkv_command mkvmerge
    set -a mkv_command --title "[LastLight] Yofukashi no Uta Season 2 - $episode"

    set chapters_file "Chapters/$episode.xml"
    if not test -e $chapters_file
        set_color red ; echo "[mux] Chapters file not found." ; set_color normal
        return 126
    end
    set -a mkv_command --chapters $chapters_file

    set output_file "Publish/[LastLight] Yofukashi no Uta Season 2 - $episode [WebRip 1080p AV1 Multi-Subs Alicia].mkv"
    set -a mkv_command --output $output_file

    set video_file "Video/$episode.mkv"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -a mkv_command --language 0:ja $video_file

    set audio_file "Audio/$episode.aac"
    if not test -e $audio_file
        set_color red ; echo "[mux] Audio file not found." ; set_color normal
        return 126
    end
    set audio_sync_file "Audio/$episode.aac.sync"
    if not test -e $audio_sync_file
        set -a mkv_command --language 0:ja --sync 0:-6006 $audio_file
    else
        set -a mkv_command --language 0:ja --sync 0:(math -6006 + (cat $audio_sync_file)) $audio_file
    end

    for subtitle_file in (find "Subtitles" -regex ".*\\[.*?\\] $episode.*" -type f)
        set group (string match --regex --groups-only "^[A-Z] \\[(.*?)\\]" (path basename $subtitle_file))
        set language (string match --regex --groups-only "$episode\\.(.*?)\\." $subtitle_file)

        if test $group = "Commie"
            set -a mkv_command --language 0:$language --track-name 0:$group $subtitle_file
        else if test $group = "Erai-raws ADN"
            set -a mkv_command --language 0:$language --track-name 0:$group --sync 0:-5005 $subtitle_file
        else
            set -a mkv_command --language 0:$language --track-name 0:$group --sync 0:-6006 $subtitle_file
        end
    end

    for f in (find "Subtitles/$episode.Fonts" -type f)
        set -a mkv_command --attach-file $f
    end
    
    set_color -o white ; echo "[mux] Muxing Yofukashi no Uta Season 2 Episode $episode..." ; set_color normal

    echo "[mux]" $mkv_command
    $mkv_command
    or return $status
    if not test -e "$output_file"
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Episode number "01"
function clean
    set episode $argv[1]
    if test -z "$episode"
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    rm -rf "logs" "Temp/$episode.boost.tmp" "Temp/$episode.scenes.json" "Temp/$episode.roi.maps" "Temp/$episode.tmp"
end
