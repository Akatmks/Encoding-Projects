#!/usr/bin/env fish

# $argv[1]: Episode number "01"
function prepare
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[prepare] Episode number not provided." ; set_color normal
        return 126
    end
    set title "[Kekkan] Kanpekiseijo - $episode"

    set prefix .

    set source_file (find $prefix -regex "$prefix/\[SubsPlease\] Kanpekiseijo - $episode (1080p) \[[0-9A-F]+\].mkv")
    if not test -e $source_file
        set_color red ; echo "[prepare] Source file not found." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[prepare] Preparing Kanpeki episode $episode..." ; set_color normal
    
    set autoboost_temp_dir "$prefix/Kanpeki $episode.autoboost.tmp"
    set output_zone_file "$autoboost_temp_dir/ssimu2_zones.txt"
    set zones_file "$prefix/Kanpeki $episode.zones.txt"
    if not test -e $zones_file
        if test -e $autoboost_temp_dir
            rm -r $autoboost_temp_dir
        end
        python auto-boost_2.5.py --input $source_file --temp $autoboost_temp_dir --quality 19 --preset 5 --video_params "--tune 3 --qm-min 9 --chroma-qm-min 8 --enable-tf 1 --kf-tf-strength 1 --tf-strength 2 --sharpness 0 --psy-rd 2.4 --spy-rd 0" --skip 2
        or return $status
        if not test -e $output_zone_file
            set_color red ; echo "[prepare] Generated zone file missing. Exiting..." ; set_color normal
            return 126
        end
    end
    cp $output_zone_file $zones_file

    set keyframes_file "$prefix/Kanpeki $episode.keyframes.txt"
    set error_file "$prefix/Kanpeki $episode.error.txt"
    set frame_diff_file "$prefix/Kanpeki $episode.frame diff.txt"
    if begin not test -e $error_file; or not test -e $frame_diff_file; end
        SOURCE_FILE=$source_file KEYFRAMES_FILE=$keyframes_file ERROR_FILE=$error_file FRAME_DIFF_FILE=$frame_diff_file python "Kanpeki-Prepare.py"
    end
    if not test -e $error_file
        set_color red ; echo "[prepare] Generated error file missing. Exiting..." ; set_color normal
        return 126
    end
    if not test -e $frame_diff_file
        set_color red ; echo "[prepare] Generated frame diff file missing. Exiting..." ; set_color normal
        return 126
    end

    set temp_dir "$prefix/Kanpeki $episode.prepare.tmp"
    if test -e $temp_dir
        rm -r $temp_dir
    end
    set scenes_file "$prefix/Kanpeki $episode.scenes.json"
    if not test -e $scenes_file
        av1an -y --max-tries 5 --temp $temp_dir --verbose --log-level debug -i $source_file --sc-only --scenes $scenes_file --extra-split 360 --min-scene-len 24 --zones $zones_file --encoder svt-av1 --video-params "--keyint -1 --input-depth 10 --tune 3 --qm-min 9 --chroma-qm-min 8 --enable-tf 1 --kf-tf-strength 1 --tf-strength 2 --sharpness 0 --film-grain 7 --spy-rd 0 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0"
    end
    if not test -e $scenes_file
        set_color red ; echo "[prepare] Generated scenes file missing. Exiting..." ; set_color normal
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

    set prefix .

    set source_file (find $prefix -regex "$prefix/\[SubsPlease\] Kanpekiseijo - $episode (1080p) \[[0-9A-F]+\].mkv")
    if not test -e $source_file
        set_color red ; echo "[encode] Source file not found." ; set_color normal
        return 126
    end
    
    set scenes_file "$prefix/Kanpeki $episode.scenes.json"
    if not test -e $scenes_file
        set_color red ; echo "[encode] Scenes file not found." ; set_color normal
        return 126
    end
    
    set zones_file "$prefix/Kanpeki $episode.zones.txt"
    if not test -e $zones_file
        set_color red ; echo "[encode] Zones file not found." ; set_color normal
        return 126
    end
    
    set error_file "$prefix/Kanpeki $episode.error.txt"
    if not test -e $error_file
        set_color red ; echo "[encode] Error file not found." ; set_color normal
        return 126
    end

    set frame_diff_file "$prefix/Kanpeki $episode.frame diff.txt"
    if not test -e $frame_diff_file
        set_color red ; echo "[encode] Frame diff file not found." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[encode] Encoding Kanpeki episode $episode..." ; set_color normal
    
    set_color -o magenta ; echo "[encode] Encoding server starting for episode $episode..." ; set_color normal
    EPISODE=$episode USAGE=$usage python Kanpeki-Server.py &
    
    set video_file "$prefix/Kanpeki $episode.mkv"
    if test -e $video_file
        set_color -o yellow ; echo "[encode] Target video file already exists. Continuing..." ; set_color normal
    end
    set temp_dir "$prefix/Kanpeki $episode.tmp"
    if test -e $temp_dir
        set_color -o yellow ; echo "[encode] Temp dir already exists. Continuing..." ; set_color normal
    end
    EPISODE=$episode SOURCE_FILE=$source_file ERROR_FILE=$error_file FRAME_DIFF_FILE=$frame_diff_file av1an -y --max-tries 5 --temp $temp_dir --resume --keep --verbose --log-level debug -i "Kanpeki.py" -o $video_file --scenes $scenes_file --chunk-order random --chunk-method bestsource --workers 12 --encoder svt-av1 --video-params "[1;5m:ferncheer:[0m" --pix-format yuv420p10le --concat mkvmerge
    or return $status
    if not test -e $video_file
        set_color red ; echo "[encode] Encoded video file missing. Exiting..." ; set_color normal
        return 126
    end

    EPISODE=$episode python Kanpeki-Server-Shutdown.py
    or return $status
    set_color -o magenta ; echo "[encode] Encoding server stopped for episode $episode..." ; set_color normal
end

# $argv[1]: Episode number "01"
function shutdown
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[shutdown] Episode number not provided." ; set_color normal
        return 126
    end

    EPISODE=$episode python Kanpeki-Server-Shutdown.py
    or return $status
end

# $argv[1]: Episode number "01"
function mux
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux] Episode number not provided." ; set_color normal
        return 126
    end
    set title "[Kekkan] Kanpekiseijo - $episode"
    
    set prefix .
    
    set_color -o white ; echo "[mux] Muxing Kanpeki episode $episode..." ; set_color normal

    set subsplease_release (find $prefix -regex "$prefix/\[SubsPlease\] Kanpekiseijo - $episode (1080p) \[[0-9A-F]+\].mkv")
    if not test -e $subsplease_release
        set_color red ; echo "[mux] SubsPlease release not found." ; set_color normal
        return 126
    end

    set erai_raws_release (find $prefix -regex "$prefix/\[Erai-raws\] Kanpekiseijo - $episode \[1080p CR WEB-DL AVC AAC\]\[MultiSub\]\[[0-9A-F]+\].mkv")
    if not test -e $erai_raws_release
        set_color red ; echo "[mux] Erai-raws release not found." ; set_color normal
        return 126
    end

    set video_file "$prefix/Kanpeki $episode.mkv"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end

    set chapters_file "$prefix/Kanpeki $episode.chapters.xml"
    if not test -e $chapters_file
        set_color red ; echo "[mux] Chapters file not found." ; set_color normal
        return 126
    end

    set output_file "$prefix/Publish/$title (WebRip 1080p AV1 Multi-Subs Alicia).mkv"
    mkvmerge --title $title --chapters $chapters_file --output $output_file --language 0:jpn $video_file --no-video --no-chapters --no-global-tags $subsplease_release --no-video --no-audio --subtitle-tracks !2 --no-chapters --no-global-tags $erai_raws_release
    or return $status
    if not test -e $output_file
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Episode number "01"
function clean
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    set prefix .

    rm -rf "logs" "$prefix/Kanpeki $episode.autoboost.tmp" (find $prefix -regex "$prefix/\[SubsPlease\] Kanpekiseijo - $episode (1080p) \[[0-9A-F]+\]_fastpass.mkv") (find $prefix -regex "$prefix/\[SubsPlease\] Kanpekiseijo - $episode (1080p) \[[0-9A-F]+\]_ssimu2.log") "$prefix/Kanpeki $episode.prepare.tmp" "$prefix/Kanpeki $episode.tmp"
end
