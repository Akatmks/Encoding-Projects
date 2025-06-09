#!/usr/bin/env fish

# $argv[1]: Full path to input m2ts relative to the root
# $argv[2]: Output subdirectory
# $argv[3]: Output episode name "01" or "Extra Episode 01" or "NCOP"
# $argv[4]: Video quality "Standard" or "Fast"
# $argv[5]: Audio quality "Standard" or "Lossless" or "Low"
function prepare
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[prepare] Source file not found." ; set_color normal
        return 126
    end
    set name $argv[3]
    if test -z $name
        set_color red ; echo "[prepare] Episode name is required." ; set_color normal
        return 126
    end
    set video_quality $argv[4]
    if begin not test $video_quality = "Standard" ; and not test $video_quality = "Fast" ; and not test $video_quality = "Fast-Vertical" ; end
        set_color red ; echo "[encode_audio] Invalid video quality." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[prepare] Preparing Euphonium - $name..." ; set_color normal
    echo "[prepare] $source_file"

    set lwi_file "Temps/$name.lwi"
    set scenes_file "Temps/$name.scenes.json"
    set temp_dir_boost "Temps/$name.boost.tmp"
    if not test -e $scenes_file
        set_color -o magenta ; echo "[prepare] Starting dispatch server..." ; set_color normal
        python Server.py &

        if test $video_quality = "Standard"
            SOURCE_FILE=$source_file LWI_FILE=$lwi_file python Progression-Boost.py --input $source_file --input-lwi $lwi_file --encode-input "Euphonium-Boost.py" --output-scenes $scenes_file --temp $temp_dir_boost --resume
            or begin set status_ $status
                python Server-Shutdown.py
                set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal
                return $status_
            end
        else if test $video_quality = "Fast"
            SOURCE_FILE=$source_file LWI_FILE=$lwi_file python Progression-Boost-Fast.py --input $source_file --input-lwi $lwi_file --encode-input "Euphonium-Boost.py" --output-scenes $scenes_file --temp $temp_dir_boost --resume
            or begin set status_ $status
                python Server-Shutdown.py
                set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal
                return $status_
            end
        else if test $video_quality = "Fast-Vertical"
            SOURCE_FILE=$source_file LWI_FILE=$lwi_file python Progression-Boost-Fast-Vertical.py --input $source_file --input-lwi $lwi_file --encode-input "Euphonium-Boost.py" --output-scenes $scenes_file --temp $temp_dir_boost --resume
            or begin set status_ $status
                python Server-Shutdown.py
                set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal
                return $status_
            end
        end

        python Server-Shutdown.py
        or return $status
        set_color -o magenta ; echo "[prepare] Stopping dispatch server..." ; set_color normal
    end
    if not test -e $scenes_file
        set_color red ; echo "[prepare] Generated scenes file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Full path to input m2ts relative to the root
# $argv[2]: Output subdirectory
# $argv[3]: Output episode name "01" or "Extra Episode 01" or "NCOP"
# $argv[4]: Video quality "Standard" or "Fast"
# $argv[5]: Audio quality "Standard" or "Lossless" or "Low"
# $argv[6]: CPU Usage "80" (Default)
function encode
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[encode] Source file not found." ; set_color normal
        return 126
    end
    set name $argv[3]
    if test -z $name
        set_color red ; echo "[encode] Episode name is required." ; set_color normal
        return 126
    end
    set usage $argv[6]
    if test -z $usage
        set usage 80
    end

    set scenes_file "Temps/$name.scenes.json"
    if not test -e $scenes_file
        set_color red ; echo "[encode] Scenes file not found." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[encode] Encoding Euphonium - $name..." ; set_color normal
    echo "[encode] $source_file"
    
    set_color -o magenta ; echo "[encode] Starting dispatch server..." ; set_color normal
    USAGE=$usage python Server.py &
    
    set video_file "Video/$name.mkv"
    if test -e $video_file
        set_color -o yellow ; echo "[encode] Target video file already exists. Continuing..." ; set_color normal
    end
    set lwi_file "Temps/$name.lwi"
    set temp_dir "Temps/$name.tmp"
    if test -e $temp_dir
        set_color -o yellow ; echo "[encode] Temp dir already exists. Continuing..." ; set_color normal
    end
    SOURCE_FILE=$source_file LWI_FILE=$lwi_file av1an -y --max-tries 5 --temp $temp_dir --resume --keep --verbose --log-level debug -i "Euphonium.py" -o $video_file --scenes $scenes_file --chunk-order random --chunk-method lsmash --workers 10 --encoder svt-av1 --no-defaults --video-params "[1;5m:kumikana:[0m" --pix-format yuv420p10le --concat mkvmerge
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

# $argv[1]: Full path to input m2ts relative to the root
# $argv[2]: Output subdirectory
# $argv[3]: Output episode name "01" or "Extra Episode 01" or "NCOP"
# $argv[4]: Video quality "Standard" or "Fast"
# $argv[5]: Audio quality "Standard" or "Lossless" or "Low"
function encode_audio
    set source_file $argv[1]
    if not test -e $source_file
        set_color red ; echo "[encode_audio] Source file not found." ; set_color normal
        return 126
    end
    set name $argv[3]
    if test -z $name
        set_color red ; echo "[encode_audio] Episode name is required." ; set_color normal
        return 126
    end
    set audio_quality $argv[5]
    if begin not test $audio_quality = "Standard" ; and not test $audio_quality = "Lossless" ; and not test $audio_quality = "Low" ; end
        set_color red ; echo "[encode_audio] Invalid audio quality." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[encode_audio] Encoding Euphonium - $name..." ; set_color normal
    echo "[encode_audio] $source_file"

    set audio_file_flac "Audio/$name.flac"
    set audio_file_flac_win "Audio\\$name.flac"
    set audio_file_opus "Audio/$name.opus"
    if not test -e $audio_file_flac
        eac3to $source_file 2: $audio_file_flac_win -normal -log=/dev/null
        or return $status
    end

    if test $audio_quality = "Standard"
        opusenc $audio_file_flac $audio_file_opus --bitrate 256
        or return $status
    else if test $audio_quality = "Low"
        opusenc $audio_file_flac $audio_file_opus --bitrate 128
        or return $status
    end
end

# [KanadeBestGirl] Hibike! Euphonium 3 (BDRip 1080p AV1 JPN CHS CHT ENG Alicia)/
#   [KanadeBestGirl] Hibike! Euphonium 3 - 01 (BDRip 1080p AV1 JPN CHS CHT ENG Alicia).mkv
#   Extra Episodes/[KanadeBestGirl] Hibike! Euphonium 3 - Extra Episode 01 (BDRip 1080p AV1 JPN ENG Alicia).mkv
#   NCOP & NCED/[KanadeBestGirl] Hibike! Euphonium 3 - NCOP01 (BDRip 1080p AV1 FLAC JPN Alicia).mkv
#   Making & Unused Scenes/[KanadeBestGirl] Hibike! Euphonium 3 - NCOP01 (BDRip 1080p AV1 FLAC JPN Alicia).mkv

# $argv[1]: Full path to input m2ts relative to the root
# $argv[2]: Output subdirectory
# $argv[3]: Output episode name "01" or "Extra Episode 01" or "NCOP"
# $argv[4]: Video quality "Standard" or "Fast"
# $argv[5]: Audio quality "Standard" or "Lossless" or "Low"
function mux
    set output_root_dir "Publish/[KanadeBestGirl] Hibike! Euphonium 3 (BDRip 1080p AV1 JPN CHS CHT ENG Alicia)"
    set output_subdir $argv[2]
    set output_dir "$output_root_dir/$output_subdir"
    if not test -e $output_dir
        mkdir --parents $output_dir
        or return $status
    end
    set name $argv[3]
    if test -z $name
        set_color red ; echo "[mux] Episode name is required." ; set_color normal
        return 126
    end
    set mkv_output_arguments --title
    set -a mkv_output_arguments "[KanadeBestGirl] Hibike! Euphonium 3 - $name"
    set output_filename "[KanadeBestGirl] Hibike! Euphonium 3 - $name (BDRip 1080p"

    set video_file "Video/$name.mkv"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set output_filename "$output_filename AV1"

    set audio_quality $argv[5]
    if begin not test $audio_quality = "Standard" ; and not test $audio_quality = "Lossless" ; and not test $audio_quality = "Low" ; end
        set_color red ; echo "[encode_audio] Invalid audio quality." ; set_color normal
        return 126
    end

    set video_file "Video/$name.mkv"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -a mkv_input_arguments --language 0:ja $video_file

    if test $audio_quality = "Standard"
        set audio_file "Audio/$name.opus"
    else if test $audio_quality = "Lossless"
        set audio_file "Audio/$name.flac"

        set output_filename "$output_filename FLAC"

    else if test $audio_quality = "Low"
        set audio_file "Audio/$name.opus"
    end
    if not test -e $audio_file
        set_color red ; echo "[mux] Audio file not found." ; set_color normal
        return 126
    end
    set -a mkv_input_arguments --language 0:ja $audio_file
    
    set_color -o white ; echo "[mux] Muxing Euphonium - $name..." ; set_color normal

    set chapters_file "Chapters/$name.txt"
    if test -e chapters_file
        set -a mkv_output_arguments --chapters
        set -a mkv_output_arguments $chapters_file
    end

    set subtitle_file_JPN "Subtitles/$name.jpn.sup"
    if test -e $subtitle_file_JPN
        set output_filename "$output_filename JPN"
        set -a mkv_input_arguments --language 0:ja --hearing-impaired-flag 0:1 $subtitle_file_JPN
    end
    set subtitle_file_CHS "Subtitles/$name.chs.ass"
    set subtitle_file_CHT "Subtitles/$name.cht.ass"
    set subtitle_file_ENG "Subtitles/$name.eng.ass"
    if test -e $subtitle_file_CHS
        set output_filename "$output_filename CHS"
        set -a mkv_input_arguments --language 0:zh-CN --track-name 0:"北宇治字幕组・简日双语" $subtitle_file_CHS
    end
    if test -e $subtitle_file_CHT
        set output_filename "$output_filename CHT"
        set -a mkv_input_arguments --language 0:zh-TW --track-name 0:"北宇治字幕組・繁日雙語" $subtitle_file_CHT
    end
    if test -e $subtitle_file_ENG
        set output_filename "$output_filename ENG"
        set -a mkv_input_arguments --language 0:en --track-name 0:"Virtuality / TakaNishi" $subtitle_file_ENG
    end
    if begin test -e $subtitle_file_CHS ; or test -e $subtitle_file_CHT ; or test -e $subtitle_file_ENG ; end
        set subtitle_fonts_dirname (string replace --regex "[0-9][0-9]" "Fonts" $name)
        for f in (find "Subtitles/$subtitle_fonts_dirname" -type f)
            set -a mkv_input_arguments --attach-file $f
        end
    end

    set output_filename "$output_filename Alicia).mkv"
    set mkv_command mkvmerge $mkv_output_arguments --output "$output_dir/$output_filename" $mkv_input_arguments
    echo "[mux]" $mkv_command
    $mkv_command
    or return $status
    if not test -e "$output_dir/$output_filename"
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Full path to input m2ts relative to the root
# $argv[2]: Output subdirectory
# $argv[3]: Output episode name "01" or "Extra Episode 01" or "NCOP"
# $argv[4]: Video quality "Standard" or "Fast"
# $argv[5]: Audio quality "Standard" or "Lossless" or "Low"
function clean
    set name $argv[3]
    if test -z $name
        set_color red ; echo "[clean] Episode name is required." ; set_color normal
        return 126
    end

    rm -rf "logs" "Temps/$name.scenes.json" "Temps/$name.boost.tmp" "Temps/$name.tmp" "Temps/$name.lwi"
end
