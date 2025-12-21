#!/usr/bin/env fish


# $argv[1]: Episode number "01"
function filter
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[filter] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[filter] Filtering $episode..." ; set_color normal

    set intermediate_file "Intermediate/$episode.mkv"
    if test -e $intermediate_file
        set_color red ; echo "[filter] Intermediate file already exists. Exiting..." ; set_color normal
        return 126
    end
    EPISODE=$episode VSPipe filter.py -c y4m - | x264 --threads 12 --demuxer y4m --output-csp i420 --output-depth 10 --qp 0 --preset slow --colorprim bt709 --transfer bt709 --colormatrix bt709 --output $intermediate_file -
    or return $status
    if not test -e $intermediate_file
        set_color red ; echo "[filter] Intermediate file missing. Exiting..." ; set_color normal
        return 126
    end
end


# $argv[1]: Episode number "01"
function boost
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[boost] Episode number not provided." ; set_color normal
        return 126
    end

    set intermediate_file "Intermediate/$episode.mkv"
    if not test -e $intermediate_file
        set_color red ; echo "[boost] Intermediate file not found." ; set_color normal
        return 126
    end
    set intermediate_ffindex_file "Intermediate/$episode.mkv.ffindex"

    set_color -o white ; echo "[boost] Boosting $episode..." ; set_color normal

    set temp_dir_boost "Temp/$episode.boost.tmp"
    set scenes_file "Temp/$episode.scenes.json"
    SOURCE_FILE=$intermediate_file SOURCE_FFINDEX_FILE=$intermediate_ffindex_file python progression_boost.py --temp $temp_dir_boost --resume -v --encode-input mini_boost.py --output-scenes $scenes_file
    or return $status
    if not test -e $scenes_file
        set_color red ; echo "[boost] Generated scenes file missing. Exiting..." ; set_color normal
        return 126
    end
end


# $argv[1]: Episode number "01"
# $argv[2]: CPU Usage "83.333" (Default)
function encode
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end
    set usage $argv[2]
    if test -z $usage
        set usage 85
    end

    set intermediate_file "Intermediate/$episode.mkv"
    if not test -e $intermediate_file
        set_color red ; echo "[boost] Intermediate file not found." ; set_color normal
        return 126
    end
    set intermediate_ffindex_file "Intermediate/$episode.mkv.ffindex"

    set scenes_file "Temp/$episode.scenes.json"
    if not test -e $scenes_file
        set_color red ; echo "[encode] Scenes file not found." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal
    
    set_color -o magenta ; echo "[encode] Starting dispatch server..." ; set_color normal
    USAGE=$usage python server.py &
    
    set video_file "Video/$episode.mkv"
    if test -e $video_file
        set_color -o yellow ; echo "[encode] Target video file already exists. Continuing..." ; set_color normal
    end
    set temp_dir "Temp/$episode.tmp"
    if test -e $temp_dir
        set_color -o yellow ; echo "[encode] Temp dir already exists. Continuing..." ; set_color normal
    end
    SOURCE_FILE=$intermediate_file SOURCE_FFINDEX_FILE=$intermediate_ffindex_file av1an -y --max-tries 5 --temp $temp_dir --resume --keep --verbose --log-level debug -i mini_encode.py -o $video_file --scenes $scenes_file --chunk-order random --chunk-method bestsource --workers 10 --encoder svt-av1 --no-defaults --video-params "[1;5m:akuma-sama:[0m" --pix-format yuv420p10le --concat mkvmerge
    or begin set status_ $status
        python server_shutdown.py
        set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal
        return $status_
    end

    python server_shutdown.py
    or return $status
    set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal

    if not test -e $video_file
        set_color red ; echo "[encode] Encoded video file missing. Exiting..." ; set_color normal
        return 126
    end
end


function shutdown
    python server_shutdown.py
    or return $status
end


# $argv[1]: Episode number "01"
function mux
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux] Episode number not provided." ; set_color normal
        return 126
    end

    set title "[Kekkan] Tensei Akujo no Kuro Rekishi - $episode"

    set source_e (find $RAWS_DIRECTORY -regex ".*/\[E.* - $episode .*\.mkv")
    if begin test -z $source_e ; or not test -e $source_e ; end
        set_color red ; echo "[mux] Source E not found." ; set_color normal
        return 126
    end

    set source_s (find $RAWS_DIRECTORY -regex ".*/\[S.* - ""$episode""v2 .*\.mkv")
    if begin test -z $source_s ; or not test -e $source_s ; end
        set source_s (find $RAWS_DIRECTORY -regex ".*/\[S.* - $episode .*\.mkv")
    end
    if begin test -z $source_s ; or not test -e $source_s ; end
        set_color red ; echo "[mux] Source S not found." ; set_color normal
        return 126
    end

    set video_file "Video/$episode.mkv"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[mux] Muxing $episode..." ; set_color normal

    set output_file "Publish/$title (WebRip 1080p AV1 Multi-Subs Alicia).mkv"
    mkvmerge --title $title --output $output_file --language 0:jpn $video_file --no-video --no-audio --no-chapters --no-global-tags $source_s --no-video --subtitle-tracks !2 --no-chapters --no-attachments --no-global-tags $source_e
    or return $status
    if not test -e $output_file
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Episode number "01"
function clean
    set --erase clean_intermediate
    if test $argv[1] = "intermediate"
        set episode $argv[2]
        set clean_intermediate "1"
    else
        set episode $argv[1]
    end
    if test -z $episode
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    rm -rf "logs" "__pycache__" "Temp/$episode.boost.tmp" "Temp/$episode.scenes.json" "Temp/$episode.tmp"

    if test -n "$clean_intermediate"
        rm -f "Intermediate/$episode.mkv" "Intermediate/$episode.mkv.ffindex"
    end
end
