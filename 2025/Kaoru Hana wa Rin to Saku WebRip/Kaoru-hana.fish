#!/usr/bin/env fish

# $argv[1]: Input file
function extract
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[subtitle] Source file not found." ; set_color normal
        return 126
    end

    set --erase french
    set --erase group
    set --erase group2
    set --erase episode

    set french (string match --regex --groups-only "BLOOM S01E(\\d+) VOSTFR" $source_file)
    if test -n "$french"
        set group "KHFR"
        set episode $french
    end
    
    if test -z "$group"
        set group (string match --regex --groups-only "^\[(.*?)\]" (path basename $source_file))
    end
    if test -z "$group"
        set_color red ; echo "[extract] Unable to match group from filename..." ; set_color normal
        return 126
    end

    if test $group = "Haruhana"
        set group "拨雪寻春・简日双语"
        set group2 "撥雪尋春・繁日雙語"
    else if test $group = "Erai-raws"
        set group "NF"
        set group2 "NF (CC)"
    end

    if test -z "$episode"
        set episode (string match --regex --groups-only "Kaoru Hana wa Rin to Saku - (\\d+)" $source_file)
    end
    if test -z "$episode"
        set episode (string match --regex --groups-only "Kaoru Hana wa Rin to Saku - S01E(\\d+)" $source_file)
    end
    if test -z "$episode"
        set_color red ; echo "[extract] Unable to match episode number from filename..." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[extract] Extracting subtitles for Kaoru Hana - $episode..." ; set_color normal
    echo "[extract] Group:" $group
    if test -n "$group2"
        echo "[extract] Group2:" $group2
    end
    echo "[extract] Episode:" $episode

    mkvextract $source_file tracks 2:"Subtitles/[$group] $episode.ass"
    if test -n "$group2"
        mkvextract $source_file tracks 3:"Subtitles/[$group2] $episode.ass"
    end

    set fonts_dir "Subtitles/$episode.Fonts"
    mkdir $fonts_dir
    begin cd $fonts_dir
        ffmpeg -hide_banner -y -dump_attachment:t "" -i $source_file
        prevd
    end

    if test $group = "Erai-raws"
        set_color -o white ; echo "[extract] Extracting audio for Kaoru Hana - $episode..." ; set_color normal

        set audio_file "Audio/$episode.aac"
        mkvextract $source_file tracks 1:$audio_file
    end
end

# $argv[1]: Input file
function filter
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[filter] Source file not found." ; set_color normal
        return 126
    end

    set episode (string match --regex --groups-only "\\[Erai-raws\\] Kaoru Hana wa Rin to Saku - (\\d+)" $source_file)
    if test -z "$episode"
        set_color red ; echo "[filter] Unable to match episode number from filename..." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[filter] Filtering Kaoru Hana - $episode..." ; set_color normal

    set source_lwi_file "Temp/$episode.source.lwi"
    set intermediate_file "Video/$episode.intermediate.mp4"
    if test -e $intermediate_file
        set_color red ; echo "[filter] Intermediate file already exists. Exiting..." ; set_color normal
        return 126
    end
    SOURCE_FILE=$source_file SOURCE_LWI_FILE=$source_lwi_file VSPipe Kaoru-hana.py -c y4m - | x264_x64 --threads 12 --demuxer y4m --output-csp i420 --output-depth 10 --qp 0 --preset slow --colorprim bt709 --transfer bt709 --colormatrix bt709 --output $intermediate_file -
    or return $status
end

# $argv[1]: Episode number "01"
function boost
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[boost] Episode number not provided." ; set_color normal
        return 126
    end

    set intermediate_file "Video/$episode.intermediate.mp4"
    if begin test -z $intermediate_file ; or not test -e $intermediate_file ; end
        set_color red ; echo "[boost] Intermediate file not found." ; set_color normal
        return 126
    end
    set intermediate_lwi_file "Temp/$episode.intermediate.lwi"

    set_color -o white ; echo "[boost] Calculating boost for Kaoru Hana - $episode..." ; set_color normal

    set temp_dir_boost "Temp/$episode.boost.tmp"
    set scenes_file "Temp/$episode.scenes.json"
    set roi_maps_dir "Temp/$episode.roi.maps"
    SOURCE_FILE=$intermediate_file SOURCE_LWI_FILE=$intermediate_lwi_file python Progression-Boost.py --temp $temp_dir_boost --resume --input $intermediate_file --input-lwi $intermediate_lwi_file --encode-input Kaoru-hana.Boost.py --output-scenes $scenes_file --output-roi-maps $roi_maps_dir
    or return $status
    if not test -e $scenes_file
        set_color red ; echo "[boost] Generated scenes file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Episode number "01"
# $argv[2]: CPU Usage "80" (Default)
function encode
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end
    set usage $argv[2]
    if test -z $usage
        set usage 80
    end

    set intermediate_file "Video/$episode.intermediate.mp4"
    if begin test -z $intermediate_file ; or not test -e $intermediate_file ; end
        set_color red ; echo "[boost] Intermediate file not found." ; set_color normal
        return 126
    end
    set intermediate_lwi_file "Temp/$episode.intermediate.lwi"

    set scenes_file "Temp/$episode.scenes.json"
    if begin test -z $scenes_file ; or not test -e $scenes_file ; end
        set_color red ; echo "[boost] Scenes file not found." ; set_color normal
        return 126
    end
    set roi_maps_dir "Temp/$episode.roi.maps"
    if begin test -z $roi_maps_dir ; or not test -e $roi_maps_dir ; end
        set_color red ; echo "[boost] ROI map directory not exists." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding Kaoru Hana - $episode..." ; set_color normal
    
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
    SOURCE_FILE=$intermediate_file SOURCE_LWI_FILE=$intermediate_lwi_file av1an -y --max-tries 5 --temp $temp_dir --resume --keep --verbose --log-level debug -i Kaoru-hana.Encode.py -o $video_file --scenes $scenes_file --chunk-order random --chunk-method lsmash --workers 10 --encoder svt-av1 --no-defaults --video-params "[1;5m:hanasaku:[0m" --pix-format yuv420p10le --concat mkvmerge
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
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end

    set mkv_command mkvmerge
    set -a mkv_command --title "[HanaEncode] Kaoru Hana wa Rin to Saku - $episode"

    set chapters_file "Chapters/$episode.xml"
    if not test -e $chapters_file
        set_color red ; echo "[mux] Chapters file not found." ; set_color normal
        return 126
    end
    set -a mkv_command --chapters $chapters_file

    set output_file "Publish/[HanaEncode] Kaoru Hana wa Rin to Saku - $episode (WEB 1080p AV1 Multi-Subs Alicia).mkv"
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
    set -a mkv_command --language 0:ja $audio_file

    set subtitle_file_PT_BR "Subtitles/[SubVision] $episode.ass"
    if test -e $subtitle_file_PT_BR
        set -a mkv_command --language 0:pt-BR --track-name 0:"SubVision" $subtitle_file_PT_BR
    else
        set_color red ; echo "[mux] SubVision subtitle not found. Continuing..." ; set_color normal
    end

    set subtitle_file_FR "Subtitles/[KHFR] $episode.ass"
    if test -e $subtitle_file_FR
        set -a mkv_command --language 0:fr --track-name 0:"KHFR" $subtitle_file_FR
    else
        set_color red ; echo "[mux] KHFR subtitle not found. Continuing..." ; set_color normal
    end

    set subtitle_file_ZH_CN "Subtitles/[拨雪寻春・简日双语] $episode.ass"
    if test -e $subtitle_file_ZH_CN
        set -a mkv_command --language 0:zh-CN --track-name 0:"拨雪寻春・简日双语" $subtitle_file_ZH_CN
    else
        set_color red ; echo "[mux] 拨雪寻春・简日双语 subtitle not found. Continuing..." ; set_color normal
    end

    set subtitle_file_ZH_TW "Subtitles/[撥雪尋春・繁日雙語] $episode.ass"
    if test -e $subtitle_file_ZH_TW
        set -a mkv_command --language 0:zh-TW --track-name 0:"撥雪尋春・繁日雙語" $subtitle_file_ZH_TW
    else
        set_color red ; echo "[mux] 撥雪尋春・繁日雙語 subtitle not found. Continuing..." ; set_color normal
    end

    set subtitle_file_ES "Subtitles/[DantalianSubs] $episode.ass"
    if test -e $subtitle_file_ES
        set -a mkv_command --language 0:es-419 --track-name 0:"DantalianSubs" $subtitle_file_ES
    end

    set subtitle_file_JA "Subtitles/[NF] $episode.ass"
    if test -e $subtitle_file_JA
        set -a mkv_command --language 0:ja --track-name 0:"NF" $subtitle_file_JA
    else
        set_color red ; echo "[mux] NF subtitle not found. Continuing..." ; set_color normal
    end

    set subtitle_file_JA_CC "Subtitles/[NF (CC)] $episode.ass"
    if test -e $subtitle_file_JA_CC
        set -a mkv_command --language 0:ja --track-name 0:"NF (CC)" --hearing-impaired-flag 0:1 $subtitle_file_JA_CC
    else
        set_color red ; echo "[mux] NF (CC) subtitle not found. Continuing..." ; set_color normal
    end

    for f in (find "Subtitles/$episode.Fonts" -type f)
        set -a mkv_command --attach-file $f
    end
    
    set_color -o white ; echo "[mux] Muxing Kaoru Hana episode $episode..." ; set_color normal

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
    set --erase clean_intermediate
    if test $argv[1] = "intermediate"
        set episode $argv[2]
        set clean_intermediate "Yes"
    else
        set episode $argv[1]
    end
    if test -z $episode
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    rm -rf "logs" "__pycache__" "Temp/$episode.source.lwi" "Temp/$episode.intermediate.lwi" "Temp/$episode.boost.tmp" "Temp/$episode.scenes.json" "Temp/$episode.roi.maps" "Temp/$episode.tmp"

    if test -n "$clean_intermediate"
        rm "Video/$episode.intermediate.mp4"
    end
end
