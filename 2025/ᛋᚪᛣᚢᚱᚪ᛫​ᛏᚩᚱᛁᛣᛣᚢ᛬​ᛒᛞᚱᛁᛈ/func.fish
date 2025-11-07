#!/usr/bin/env fish

# $argv[1]: Episode number "01"
function audio
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[filter] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[filter] Making audio for $episode..." ; set_color normal

    set source_file (python information.py source $episode)
    or return $status
    set trim_start (python information.py trim_start $episode)
    or return $status
    set main_audio_file "Main/$episode.flac"
    set main_audio_file_win "Main\\$episode.flac"
    if test $trim_start = None
        eac3to (python information.py source $episode) 2: $main_audio_file_win -normal -log=/dev/null
        or return $status
    else
        eac3to (python information.py source $episode) 2: $main_audio_file_win -(math $trim_start / 24 "*" 1001)ms -normal -log=/dev/null
        or return $status
    end

    set mini_audio_file "Mini/$episode.opus"
    opusenc $main_audio_file $mini_audio_file --bitrate 128
end


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
    EPISODE=$episode python intermediate.py
    or return $status
    if not test -e $intermediate_file
        set_color red ; echo "[filter] Intermediate file missing. Exiting..." ; set_color normal
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
        set usage 83.333
    end

    set intermediate_file "Intermediate/$episode.mkv"
    if not test -e $intermediate_file
        set_color red ; echo "[encode] Intermediate file not found." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Boosting $episode..." ; set_color normal

    set mini_boost_dir "Temp/$episode.boost.tmp"
    set mini_scenes_file "Temp/$episode.scenes.json"
    set mini_roi_maps_dir "Temp/$episode.roi.maps"
    EPISODE=$episode python progression_boost.py --temp $mini_boost_dir --resume --episode $episode --encode-input mini_boost.py --output-scenes $mini_scenes_file --output-roi-maps $mini_roi_maps_dir
    or return $status
    if begin not test -e $mini_scenes_file; or not test -e $mini_roi_maps_dir; end
        set_color red ; echo "[encode] Boosting result missing. Exiting..." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set main_output_file "Main/$episode.265"
    if test -e $main_output_file
        set_color red ; echo "[encode] Main encode file already exists. Skipping main encode..." ; set_color normal
        return 126
    else
        EPISODE=$episode python main.py &
    end

    set_color -o magenta ; echo "[encode] Starting dispatch server..." ; set_color normal
    USAGE=$usage python server.py &

    set mini_output_file "Mini/$episode.mkv"
    if test -e $mini_output_file
        set_color red ; echo "[encode] Mini encode file already exists. Continuing..." ; set_color normal
    end
    set av1an_temp_dir "Temp/$episode.av1an.tmp"
    if test -e $av1an_temp_dir
        set_color -o yellow ; echo "[encode] Temp dir already exists. Continuing..." ; set_color normal
    end
    EPISODE=$episode av1an -y --max-tries 5 --temp $av1an_temp_dir --resume --keep --verbose --log-level debug -i mini.py -o $mini_output_file --scenes $mini_scenes_file --chunk-order random --chunk-method ffms2 --workers 10 --encoder svt-av1 --no-defaults --video-params "[1;5m:hanasaku:[0m" --pix-format yuv420p10le --concat mkvmerge

    set_color -o magenta ; echo "[encode] Stopping dispatch server..." ; set_color normal
    python server_shutdown.py

    wait

    if not test -e $main_output_file
        set_color red ; echo "[encode] Main encode file missing. Exiting..." ; set_color normal
    end
    if not test -e $mini_output_file
        set_color red ; echo "[encode] Mini encode file missing. Exiting..." ; set_color normal
    end
    if begin not test -e $main_output_file; or not test -e $mini_output_file; end
        return 126
    end
end


# $argv[1]: Episode number "01"
function clean
    set --erase clean_ia
    if test $argv[1] = "ia"
        set episode $argv[2]
        set clean_ia "1"
    else
        set episode $argv[1]
    end
    if test -z $episode
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    rm -rf "logs" "__pycache__" "Temp/$episode.x265_log.csv" "Temp/$episode.boost.tmp" "Temp/$episode.scenes.json" "Temp/$episode.roi.maps" "Temp/$episode.av1an.tmp"

    if test -n "$clean_ia"
        rm -f "Intermediate/$episode.mkv" "Intermediate/$episode.mkv.ffindex" "Main/$episode.flac" "Mini/$episode.opus"
    end
end
