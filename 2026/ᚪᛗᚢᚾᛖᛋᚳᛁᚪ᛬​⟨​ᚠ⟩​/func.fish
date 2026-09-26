#!/usr/bin/env fish


# $argv[1]: Episode number "01"
function encode
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set video_file "Video/$episode.ivf"
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
function encode_ova
    set episode OVA

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set video_file "Video/$episode.ivf"
    if test -e $video_file
        set_color red ; echo "[encode] Video file already exists. Exiting..." ; set_color normal
        return 126
    end
    python encode_ova.py
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

    set -g mkv_command mkvmerge --deterministic 0

    set title "[Kekkan] Amnesia - $episode"
    set -g -a mkv_command --title $title

    set chapters_file "Chapters/$episode.txt"
    set -g -a mkv_command --chapters $chapters_file

    set output_file "Publish/[Kekkan] Amnesia (BD 1080p AV1)/$title (BD 1080p AV1).mkv"
    set -g -a mkv_command --output $output_file


    set video_file "Video/$episode.ivf"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -g -a mkv_command --language 0:ja --track-name 0:"Kekkan" $video_file



    set source_file (EPISODE=$episode python information.py source)
    if begin test -z $source_file ; or not test -e $source_file ; end
        set_color red ; echo "[mux] Source not found." ; set_color normal
        return 126
    end

    
    set temp_source_file "$TEMP_BDMV_DIRECTORY/$episode.m2ts"
    set source_audio_file "Temp/$episode.source.flac"
    set source_audio_file_win "Temp\\$episode.source.flac"
    set audio_file "Temp/$episode.opus"
    if not test -e $audio_file
        if not test -e $source_audio_file
            mv -v $source_file $temp_source_file
            or return $status
            eac3to $temp_source_file 2: $source_audio_file_win -normal -log=/dev/null
            mv -v $temp_source_file $source_file
        end
        opusenc $source_audio_file $audio_file --bitrate 192
        or return $status
    end
    set -g -a mkv_command --language 0:ja --track-name 0:"Kekkan" $audio_file


    set eng_sub_source (find $ENG_SUB_DIRECTORY -regex ".* - Episode $(string trim --left --chars "0" $episode)\\..*")
    if begin test -z $eng_sub_source ; or not test -e $eng_sub_source ; end
        set_color red ; echo "[mux] English sub not found." ; set_color normal
        return 126
    end
    set eng_sub_info "Temp/$episode.eng_sub.log"
    mpv --vo=null --ao=null --frames=1 $eng_sub_source --msg-level=all=warn --log-file=$eng_sub_info
    or return $status
    if begin not string match --regex --quiet "cplayer.*?Audio +--aid=2" (cat $eng_sub_info)
        or string match --regex --quiet "cplayer.*?Audio +--aid=3" (cat $eng_sub_info)
    end
        set_color red ; echo "[mux] English sub has unexpected number of audio tracks." ; set_color normal
        return 126
    end
    set eng_sub_file "Temp/$episode.ass"
    mkvextract $eng_sub_source tracks 3:$eng_sub_file
    if test $episode -ge 09
        python realign.py --offset -70 --output $eng_sub_file $eng_sub_file
    else
        python realign.py --offset -20 --output $eng_sub_file $eng_sub_file
    end
    set -g -a mkv_command --language 0:en --track-name 0:"MiraiAnime · Commie · Hybrid" $eng_sub_file
    set -g -a mkv_command --no-video --no-audio --no-subtitles --no-buttons --no-chapters --no-global-tags $eng_sub_source

    
    echo $mkv_command
    $mkv_command
    or return $status
    if not test -e $output_file
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end


# $argv[1]: Episode number "01"
function mux_ova
    set episode OVA

    set_color -o white ; echo "[mux] Muxing $episode..." ; set_color normal

    set -g mkv_command mkvmerge --deterministic 0

    set title "[Kekkan] Amnesia - $episode"
    set -g -a mkv_command --title $title

    set chapters_file "Chapters/$episode.txt"
    set -g -a mkv_command --chapters $chapters_file

    set output_file "Publish/[Kekkan] Amnesia (BD 1080p AV1)/$title (DVD 480p AV1).mkv"
    set -g -a mkv_command --output $output_file


    set video_file "Video/$episode.ivf"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -g -a mkv_command --aspect-ratio-factor 0:6/5 --language 0:ja --track-name 0:"Kekkan" $video_file



    set source_file (python information_ova.py source)
    if begin test -z $source_file ; or not test -e $source_file ; end
        set_color red ; echo "[mux] Source not found." ; set_color normal
        return 126
    end

    
    set temp_source_file "$TEMP_BDMV_DIRECTORY/$episode.m2ts"
    set source_audio_file "Temp/$episode.source.flac"
    set source_audio_file_win "Temp\\$episode.source.flac"
    set audio_file "Temp/$episode.opus"
    if not test -e $audio_file
        if not test -e $source_audio_file
            mv -v $source_file $temp_source_file
            or return $status
            eac3to $temp_source_file 2: $source_audio_file_win -normal -log=/dev/null
            mv -v $temp_source_file $source_file
        end
        opusenc $source_audio_file $audio_file --bitrate 192
        or return $status
    end
    set -g -a mkv_command --language 0:ja --track-name 0:"Kekkan" $audio_file


    set eng_sub_source (find $ENG_SUB_DIRECTORY -regex ".* - $(string trim --left --chars "0" $episode) .*")
    if begin test -z $eng_sub_source ; or not test -e $eng_sub_source ; end
        set_color red ; echo "[mux] English sub not found." ; set_color normal
        return 126
    end
    set eng_sub_info "Temp/$episode.eng_sub.log"
    mpv --vo=null --ao=null --frames=1 $eng_sub_source --msg-level=all=warn --log-file=$eng_sub_info
    or return $status
    if begin not string match --regex --quiet "cplayer.*?Audio +--aid=1" (cat $eng_sub_info)
        or string match --regex --quiet "cplayer.*?Audio +--aid=2" (cat $eng_sub_info)
    end
        set_color red ; echo "[mux] English sub has unexpected number of audio tracks." ; set_color normal
        return 126
    end
    set eng_sub_file "Temp/$episode.ass"
    mkvextract $eng_sub_source tracks 2:$eng_sub_file
    # if test $episode -ge 09
    #     python realign.py --offset -70 --output $eng_sub_file $eng_sub_file
    # else
    #     python realign.py --offset -20 --output $eng_sub_file $eng_sub_file
    # end
    set -g -a mkv_command --language 0:en --track-name 0:"MiraiAnime · Hybrid" $eng_sub_file
    set -g -a mkv_command --no-video --no-audio --no-subtitles --no-buttons --no-chapters --no-global-tags $eng_sub_source

    
    echo $mkv_command
    $mkv_command
    or return $status
    if not test -e $output_file
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end



function clean
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux] Episode number not provided." ; set_color normal
        return 126
    end

    rm -rf "Temp/$episode.vsmuxtools.tmp" "Temp/$episode.eng_sub.log" "Temp/$episode.ass" "Temp/$episode.source.flac" "Temp/$episode.opus" "Temp/publish.settings.toml"
end


