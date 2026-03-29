#!/usr/bin/env fish


# $argv[1]: Episode number "01"
function encode
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set video_file "Encode/$episode.264"
    if test -e $video_file
        set_color red ; echo "[encode] Video file already exists. Exiting..." ; set_color normal
        return 126
    end
    EPISODE=$episode python encode.py
    or return $status
    if not test -e $video_file
        set_color red ; echo "[encode] Video file missing. Exiting..." ; set_color normal
        return 126
    end
end


# $argv[1]: Episode number "01"
function mux
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux] Episode number not provided." ; set_color normal
        return 126
    end

    set source_file (find $RAWS_DIRECTORY -regex ".*/\[S.* \[$episode\]\[.*\.mkv")
    if begin test -z $source_file ; or not test -e $source_file ; end
        set_color red ; echo "[mux] Source not found." ; set_color normal
        return 126
    end

    set video_file "Encode/$episode.264"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end

    set intermediate_audio_file "Temp/$episode.flac"
    mkvextract $source_file tracks 1:$intermediate_audio_file
    set audio_file "Temp/$episode.aac"
    qaac64 $intermediate_audio_file -V 111 -q 2 -o $audio_file

    set chapters_file "Temp/$episode.chapters.txt"
    mkvextract $source_file chapters --simple $chapters_file

    set output_file "Publish/[SweetSub] Momentary Lily [01-14][BDRip][1080P][AVC 8bit][CHS&JPN]/[SweetSub] Momentary Lily - $episode [BDRip][1080P][AVC 8bit][CHS&JPN].mp4"
    mp4box -add $video_file -add $audio_file -chap $chapters_file -new $output_file
    if not test -e $output_file
        set_color red ; echo "[encode_h264] Output file missing. Exiting..." ; set_color normal
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

    rm -rf "__pycache__" "Temp/$episode.vsmuxtools.tmp" "Temp/$episode.aac"
end
