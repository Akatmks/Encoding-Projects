#!/usr/bin/env fish

# $argv[1]: Episode number "01"
function intermediate
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[intermediate] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[intermediate] Filtering $episode..." ; set_color normal

    set intermediate_file "$INTERMEDIATE_DIR/$episode.mkv"
    if test -e $intermediate_file
        set_color red ; echo "[intermediate] Intermediate file already exists. Exiting..." ; set_color normal
        return 126
    end
    EPISODE=$episode python intermediate.py
    or return $status
    if not test -e $intermediate_file
        set_color red ; echo "[intermediate] Intermediate file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Episode number "01"
function encode
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end

    set intermediate_file "$INTERMEDIATE_DIR/$episode.mkv"
    if not test -e $intermediate_file
        set_color red ; echo "[encode] Intermediate file not found." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set main_encode "Main/$episode.265"
    if test -e $main_encode
        set_color red ; echo "[encode] Main encode file already exists. Skipping main encode..." ; set_color normal
    else
        EPISODE=$episode python main.py &
    end

    set mini_encode "Mini/$episode.ivf"
    if test -e $mini_encode
        set_color red ; echo "[encode] Mini encode file already exists. Skipping mini encode..." ; set_color normal
    else
        EPISODE=$episode python mini.py &
    end

    wait

    if not test -e $main_encode
        set_color red ; echo "[encode] Main encode file missing. Exiting..." ; set_color normal
    end
    if not test -e $mini_encode
        set_color red ; echo "[encode] Mini encode file missing. Exiting..." ; set_color normal
    end
    if begin not test -e $main_encode; or not test -e $mini_encode; end
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


    set fonts_dir "Temp/$episode.fonts"
    if test -e $fonts_dir
        rm -r $fonts_dir
    end
    mkdir $fonts_dir

    set -g subs_mkv_command

    cp Subtitles/en/$episode.Fonts/* $fonts_dir
    set subtitle_file Subtitles/en/$episode.ass
    set subtitle_sync_file (path change-extension ".sync" $subtitle_file)
    if test -e $subtitle_sync_file
        set -g -a subs_mkv_command --sync 0:(cat $subtitle_sync_file)
    end
    set -g -a subs_mkv_command --language 0:en --track-name 0:"Tsundere" $subtitle_file

    cp Subtitles/fr/$episode.Fonts/* $fonts_dir
    set subtitle_file Subtitles/fr/$episode.ass
    set subtitle_sync_file (path change-extension ".sync" $subtitle_file)
    if test -e $subtitle_sync_file
        set -g -a subs_mkv_command --sync 0:(cat $subtitle_sync_file)
    end
    set -g -a subs_mkv_command --language 0:fr --track-name 0:"Kazuya" $subtitle_file

    cp Subtitles/de/$episode.Fonts/* $fonts_dir
    set subtitle_file Subtitles/de/$episode.ass
    set subtitle_sync_file (path change-extension ".sync" $subtitle_file)
    if test -e $subtitle_sync_file
        set -g -a subs_mkv_command --sync 0:(cat $subtitle_sync_file)
    end
    set -g -a subs_mkv_command --language 0:de --track-name 0:"Amalgam" $subtitle_file

    cp Subtitles/ja/Fonts/* $fonts_dir
    set -g -a subs_mkv_command --language 0:ja Subtitles/ja/$episode.ass

    cp Subtitles/zh/Fonts/* $fonts_dir
    set subtitle_sync_file Subtitles/zh/$episode.sync
    if test -e $subtitle_sync_file
        set -g -a subs_mkv_command --sync 0:(cat $subtitle_sync_file)
    end
    set -g -a subs_mkv_command --language 0:zh-Hans --track-name 0:"动漫国字幕组&白月字幕组" Subtitles/zh/zh-Hans.$episode.ass
    if test -e $subtitle_sync_file
        set -g -a subs_mkv_command --sync 0:(cat $subtitle_sync_file)
    end
    set -g -a subs_mkv_command --language 0:zh-Hant --track-name 0:"動漫國字幕組&白月字幕組" Subtitles/zh/zh-Hant.$episode.ass

    for f in (find $fonts_dir -type f)
        set -g -a subs_mkv_command --attach-file $f
    end


    set -g main_mkv_command mkvmerge --deterministic 0
    set -g mini_mkv_command mkvmerge --deterministic 0

    set title "☆ 桜Trick ☆ Sakura Trick ☆ S01E$episode [Himejoshi]"
    set -g -a main_mkv_command --title $title
    set -g -a mini_mkv_command --title $title

    set chapters_file "Chapters/$episode.txt"
    set -g -a main_mkv_command --chapters $chapters_file
    set -g -a mini_mkv_command --chapters $chapters_file

    set main_output_file "Publish/[Himejoshi] Sakura Trick (BD 1080p HEVC FLAC)/[Himejoshi] Sakura Trick - S01E$episode (BD 1080p HEVC FLAC).mkv"
    set mini_output_file "Publish/[Himejoshi] Sakura Trick (BD 1080p AV1)/[Himejoshi] Sakura Trick - S01E$episode (BD 1080p AV1).mkv"
    set -g -a main_mkv_command --output $main_output_file
    set -g -a mini_mkv_command --output $mini_output_file


    set main_video_file "Main/$episode.265"
    if not test -e $main_video_file
        set_color red ; echo "[mux] Main video file not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Himejoshi" $main_video_file

    set mini_video_file "Mini/$episode.ivf"
    if not test -e $mini_video_file
        set_color red ; echo "[mux] Mini video file not found." ; set_color normal
        return 126
    end
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Himejoshi" $mini_video_file
    

    set 24_bit_audio_file "Temp/$episode.24-bit.flac"
    set 24_bit_audio_file_win "Temp\\$episode.24-bit.flac"
    if not test -e $24_bit_audio_file
        eac3to (python information.py source $episode) 2: $24_bit_audio_file_win -log=/dev/null
        or return $status
    end
    set main_audio_file "Temp/$episode.flac"
    if not test -e $main_audio_file
        sox -V3 --volume 0.99 $24_bit_audio_file --bits 16 --rate 48000 --compress 8 --comment "" $main_audio_file
        or return $status
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Himejoshi" $main_audio_file

    set mini_audio_file "Temp/$episode.opus"
    if not test -e $mini_audio_file
        opusenc $main_audio_file $mini_audio_file --bitrate 160
        or return $status
    end
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Himejoshi" $mini_audio_file


    set -g -a main_mkv_command $subs_mkv_command
    set -g -a mini_mkv_command $subs_mkv_command


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

    set title "☆ 桜Trick ☆ Sakura Trick ☆ $episode [Himejoshi]"
    set -g -a main_mkv_command --title $title
    set -g -a mini_mkv_command --title $title

    set main_output_file "Publish/[Himejoshi] Sakura Trick (BD 1080p HEVC FLAC)/NCOP & NCED/[Himejoshi] Sakura Trick - $episode (BD 1080p HEVC FLAC).mkv"
    set mini_output_file "Publish/[Himejoshi] Sakura Trick (BD 1080p AV1)/NCOP & NCED/[Himejoshi] Sakura Trick - $episode (BD 1080p AV1 FLAC).mkv"
    set -g -a main_mkv_command --output $main_output_file
    set -g -a mini_mkv_command --output $mini_output_file


    set main_video_file "Main/$episode.265"
    if not test -e $main_video_file
        set_color red ; echo "[mux] Main video file not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Himejoshi" $main_video_file

    set mini_video_file "Mini/$episode.ivf"
    if not test -e $mini_video_file
        set_color red ; echo "[mux] Mini video file not found." ; set_color normal
        return 126
    end
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Himejoshi" $mini_video_file
    

    set 24_bit_audio_file "Temp/$episode.24-bit.flac"
    set 24_bit_audio_file_win "Temp\\$episode.24-bit.flac"
    if not test -e $24_bit_audio_file
        eac3to (python information.py source $episode) 2: $24_bit_audio_file_win -log=/dev/null
        or return $status
    end
    set main_audio_file "Temp/$episode.flac"
    if not test -e $main_audio_file
        sox -V3 --volume 0.99 $24_bit_audio_file --bits 16 --rate 48000 --compress 8 --comment "" $main_audio_file
        or return $status
    end
    set trim_start (python information.py trim_start $episode)
    if test $trim_start = None
        set -g -a main_mkv_command --language 0:ja --track-name 0:"Himejoshi" $24_bit_audio_file
        set -g -a mini_mkv_command --language 0:ja --track-name 0:"Himejoshi" $main_audio_file
    else
        set -g -a main_mkv_command --language 0:ja --sync 0:-(math $trim_start / 24 "*" 1001) --track-name 0:"Himejoshi" $24_bit_audio_file
        set -g -a mini_mkv_command --language 0:ja --sync 0:-(math $trim_start / 24 "*" 1001) --track-name 0:"Himejoshi" $main_audio_file
    end


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

    rm -rf "__pycache__" "Temp/$episode.vsmuxtools.tmp" "Temp/$episode.24-bit.flac" "Temp/$episode.flac" "Temp/$episode.opus" "Temp/$episode.fonts"

    if test -n "$clean_ia"
        rm -f "$INTERMEDIATE_DIR/$episode.mkv" "Main/$episode.flac" "Mini/$episode.opus"
    end
end
