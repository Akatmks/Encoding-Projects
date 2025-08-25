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
    if begin test -z $source_file ; or not test -e $source_file ; end
        set_color red ; echo "[prepare] Source file not found." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[prepare] Preparing Kanpeki episode $episode..." ; set_color normal

    set scenes_file "$prefix/Kanpeki $episode.scenes.json"
    set error_file "$prefix/Kanpeki $episode.error.txt"
    set frame_diff_file "$prefix/Kanpeki $episode.frame diff.txt"
    set temp_dir "$prefix/Kanpeki $episode.boost.tmp"
    if begin not test -e $error_file; or not test -e $frame_diff_file; or not test -e $scenes_file; end
        SOURCE_FILE=$source_file python Progression-Boost.py --input $source_file --encode-input "Kanpeki-Boost-Base.py" --output-scenes $scenes_file --output-error $error_file --output-frame-diff $frame_diff_file --temp $temp_dir --resume
    end
    if not test -e $scenes_file
        set_color red ; echo "[prepare] Generated scenes file missing. Exiting..." ; set_color normal
        return 126
    end
    if not test -e $error_file
        set_color red ; echo "[prepare] Generated error file missing. Exiting..." ; set_color normal
        return 126
    end
    if not test -e $frame_diff_file
        set_color red ; echo "[prepare] Generated frame diff file missing. Exiting..." ; set_color normal
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
    if begin test -z $source_file ; or not test -e $source_file ; end
        set_color red ; echo "[encode] Source file not found." ; set_color normal
        return 126
    end
    
    set scenes_file "$prefix/Kanpeki $episode.scenes.json"
    if not test -e $scenes_file
        set_color red ; echo "[encode] Scenes file not found." ; set_color normal
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
    if begin test -z $subsplease_release ; or not test -e $subsplease_release ; end
        set_color red ; echo "[mux] SubsPlease release not found." ; set_color normal
        return 126
    end

    set erai_raws_release (find $prefix -regex "$prefix/\[Erai-raws\] Kanpekiseijo - $episode \[1080p CR WEBRip HEVC [EAC3]+\]\[MultiSub\]\[[0-9A-F]+\].mkv")
    if begin test -z $erai_raws_release ; or not test -e $erai_raws_release ; end
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

    set fonts_dir "$prefix/Kanpeki $episode.fonts"
    if test -e $fonts_dir
        rm -r $fonts_dir
    end
    mkdir $fonts_dir
    begin cd $fonts_dir
        ffmpeg -hide_banner -y -dump_attachment:t "" -i "../$(realpath --relative-to=$prefix $erai_raws_release)"
        ffmpeg -hide_banner -y -dump_attachment:t "" -i "../$(realpath --relative-to=$prefix $subsplease_release)"
        for f in (find . -type f)
            set fonts_file (string match --regex --groups-only "^(.*)_\\d(\\.\\w+?)\$" $f)
            and begin if test -e $fonts_file[1]$fonts_file[2]
                    rm $f
                else
                    mv $f $fonts_file[1]$fonts_file[2]
                end
            end
        end
        prevd
    end

    set output_file "$prefix/Publish/$title (WebRip 1080p AV1 Multi-Subs Alicia).mkv"
    set attach_fonts
    for f in (find $fonts_dir -type f)
        set -a attach_fonts --attach-file
        set -a attach_fonts $f
    end
    mkvmerge --title $title --chapters $chapters_file --output $output_file --language 0:jpn $video_file --no-video --no-chapters --no-attachments --no-global-tags $subsplease_release --no-video --no-audio --subtitle-tracks !2 --no-chapters --no-attachments --no-global-tags $erai_raws_release $attach_fonts
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

    rm -rf "logs" "$prefix/Kanpeki $episode.boost.tmp" "$prefix/Kanpeki $episode.tmp" "$prefix/Kanpeki $episode.fonts"
end
