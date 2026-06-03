#!/usr/bin/env fish


# $argv[1]: Episode number "01"
function encode
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set video_file "Video/$episode.265"
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

    set_color -o white ; echo "[mux] Muxing $episode..." ; set_color normal


    set -g main_mkv_command mkvmerge --deterministic 0
    set -g mini_mkv_command mkvmerge --deterministic 0

    set title "[Kekkan] Champignon no Majo - $episode"
    set -g -a main_mkv_command --title $title
    set -g -a mini_mkv_command --title $title
    

    set chapters_file "Misc/Chapters/$episode.txt"
    set -g -a main_mkv_command --chapters $chapters_file
    set -g -a mini_mkv_command --chapters $chapters_file


    set -g -a main_mkv_command --track-order 0:0,1:0,3:2,3:3
    set -g -a mini_mkv_command --track-order 2:0,0:0,2:2,2:3


    set main_output_file "Publish/[Kekkan] Champignon no Majo (BDRip 1080p HEVC FLAC Multi-Subs)/$title (BDRip 1080p HEVC FLAC Multi-Subs).mkv"
    set -g -a main_mkv_command --output $main_output_file
    set mini_output_file "Publish/[Kekkan] Champignon no Majo (WEBRip 1080p AV1 Multi-Subs)/$title (WEBRip 1080p AV1 Multi-Subs).mkv"
    set -g -a mini_mkv_command --output $mini_output_file



    set main_video_file "Video/$episode.265"
    if not test -e $main_video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --language 0:jpn --track-name 0:"Kekkan" $main_video_file


    set 24_bit_audio_file "Temp/$episode.24-bit.flac"
    set 24_bit_audio_file_win "Temp\\$episode.24-bit.flac"
    if not test -e $24_bit_audio_file
        eac3to (python information.py source_bd $episode) 2: $24_bit_audio_file_win -log=/dev/null
        or return $status
    end
    set main_audio_file "Temp/$episode.flac"
    if not test -e $main_audio_file
        sox -V3 --volume 0.99 $24_bit_audio_file --bits 16 --compress 8 --comment "" $main_audio_file
        or return $status
    end
    set mini_audio_file "Temp/$episode.opus"
    if not test -e $mini_audio_file
        opusenc $main_audio_file $mini_audio_file --bitrate 160
        or return $status
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Kekkan" $main_audio_file
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Kekkan" $mini_audio_file


    set source_g (find $GREENTEA_DIR -regex ".*/\[S.* \[$episode.*\.mkv")
    if begin test -z $source_g ; or not test -e $source_g ; end
        set_color red ; echo "[mux] Source G not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --no-video --no-audio --language 2:zh-Hans --track-name 2:"绿茶字幕组" --language 3:zh-Hant --track-name 3:"綠茶字幕組" --no-buttons --no-chapters --no-global-tags $source_g
    set -g -a mini_mkv_command --no-video --no-audio --language 2:zh-Hans --track-name 2:"绿茶字幕组" --language 3:zh-Hant --track-name 3:"綠茶字幕組" --no-buttons --no-chapters --no-global-tags $source_g

    set source_k (find $KEKKAN_DIR -regex ".*/\[K.* - $episode .*\.mkv")
    if begin test -z $source_k ; or not test -e $source_k ; end
        set_color red ; echo "[mux] Source K not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --no-video --no-audio --subtitle-tracks !zh-Hans,zh-Hant --no-buttons --no-chapters --no-global-tags $source_k
    set -g -a mini_mkv_command --no-audio --subtitle-tracks !zh-Hans,zh-Hant --no-buttons --no-chapters --no-global-tags $source_k


    echo $main_mkv_command
    $main_mkv_command
    or return $status
    echo $mini_mkv_command
    $mini_mkv_command
    or return $status
    if not test -e $main_output_file
        set_color red ; echo "[mux] Main output file missing. Exiting..." ; set_color normal
    end
    if not test -e $mini_output_file
        set_color red ; echo "[mux] Mini output file missing. Exiting..." ; set_color normal
    end
    if begin not test -e $main_output_file ; or not test -e $mini_output_file ; end
        return 126
    end
end


# $argv[1]: Episode number "01"
function mux_nc
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[mux] Muxing $episode..." ; set_color normal


    set -g main_mkv_command mkvmerge --deterministic 0
    set -g mini_mkv_command mkvmerge --deterministic 0

    set title "[Kekkan] Champignon no Majo - $episode"
    set -g -a main_mkv_command --title $title
    set -g -a mini_mkv_command --title $title


    set main_output_file "Publish/[Kekkan] Champignon no Majo (BDRip 1080p HEVC FLAC Multi-Subs)/$title (BDRip 1080p HEVC FLAC).mkv"
    set -g -a main_mkv_command --output $main_output_file
    set mini_output_file "Publish/[Kekkan] Champignon no Majo (WEBRip 1080p AV1 Multi-Subs)/$title (BDRip 1080p HEVC FLAC).mkv"
    set -g -a mini_mkv_command --output $mini_output_file



    set main_video_file "Video/$episode.265"
    if not test -e $main_video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set mini_video_file "Video/$episode.mini.265"
    if not test -e $mini_video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --language 0:jpn --track-name 0:"Kekkan" $main_video_file
    set -g -a mini_mkv_command --language 0:jpn --track-name 0:"Kekkan" $mini_video_file


    set 24_bit_audio_file "Temp/$episode.24-bit.flac"
    set 24_bit_audio_file_win "Temp\\$episode.24-bit.flac"
    if not test -e $24_bit_audio_file
        eac3to (python information.py source_bd $episode) 2: $24_bit_audio_file_win -log=/dev/null
        or return $status
    end
    set main_audio_file "Temp/$episode.flac"
    if not test -e $main_audio_file
        sox -V3 --volume 0.99 $24_bit_audio_file --bits 16 --compress 8 --comment "" $main_audio_file
        or return $status
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Kekkan" $24_bit_audio_file
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Kekkan" $main_audio_file


    echo $main_mkv_command
    $main_mkv_command
    or return $status
    echo $mini_mkv_command
    $mini_mkv_command
    or return $status
    if not test -e $main_output_file
        set_color red ; echo "[mux] Main output file missing. Exiting..." ; set_color normal
    end
    if not test -e $mini_output_file
        set_color red ; echo "[mux] Mini output file missing. Exiting..." ; set_color normal
    end
    if begin not test -e $main_output_file ; or not test -e $mini_output_file ; end
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

    rm -rf "__pycache__" "Temp/$episode.vsmuxtools.tmp" "Temp/$episode.24-bit.flac" "Temp/$episode.flac" "Temp/$episode.opus"
end
