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


# $argv[1]: Subtitle file
function mux_restyle_subtitle
    set subtitle_file $argv[1]
    if begin test -z $subtitle_file ; or not test -e $subtitle_file ; end
        set_color red ; echo "[mux_restyle_subtitle] Subtitle file not found." ; set_color normal
        return 126
    end

    for style in "BottomLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,1,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomCenter" "Default" "Main" "Gen_Main" "Narration" "Narratore" "TiretsDefault" "Default overlap" "Flashback" "Main_Flashback"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,2,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomRight"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,3,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics" "Italic" "Main_Italic" "Gen_Italics" "Italique" "TiretsItalique" "Flashback Italics" "Flashback - Italics"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,-1,0,0,100,100,0,0,1,1.15,0.45,2,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,7,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopCenter" "Top" "Main_Top" "Gen_Main_Up" "Main - Top" "Flashback Top"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,8,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopRight"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,9,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics Top" "Main_Top_Italic" "Gen_Italics_top" "DefaultItalicsTop" "Flashback Italics Top" "Italics - Top" "ItalicsTop"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,-1,0,0,100,100,0,0,1,1.15,0.45,8,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,4,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterCenter"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,5,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterRight"
        string replace --regex "^Style: $style,.*" "Style: $style,Lato,24,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,-1,0,0,0,100,100,0,0,1,1.15,0.45,6,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
end

# $argv[1]: Subtitle file
function mux_restyle_subtitle_ru
    set subtitle_file $argv[1]
    if begin test -z $subtitle_file ; or not test -e $subtitle_file ; end
        set_color red ; echo "[mux_restyle_subtitle_ru] Subtitle file not found." ; set_color normal
        return 126
    end

    for style in "BottomLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,1,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomCenter" "Default" "Main" "Gen_Main" "Narration" "Narratore" "TiretsDefault" "Default overlap" "Flashback" "Main_Flashback"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,2,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomRight"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,3,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics" "Italic" "Main_Italic" "Gen_Italics" "Italique" "TiretsItalique" "Flashback Italics" "Flashback - Italics"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,-1,0,0,100,100,0,0,1,1.15,0.45,2,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,7,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopCenter" "Top" "Main_Top" "Gen_Main_Up" "Main - Top" "Flashback Top"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,8,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopRight"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,9,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics Top" "Main_Top_Italic" "Gen_Italics_top" "DefaultItalicsTop" "Flashback Italics Top" "Italics - Top" "ItalicsTop"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,-1,0,0,100,100,0,0,1,1.15,0.45,8,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,4,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterCenter"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,5,20,20,20,1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterRight"
        string replace --regex "^Style: $style,.*" "Style: $style,Fira Sans Medium,23,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,0,0,0,0,100,100,0,0,1,1.15,0.45,6,20,20,20,1" (cat $subtitle_file) > $subtitle_file
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


    set mkv_command mkvmerge

    set title "[Kekkan] Tensei Akujo no Kuro Rekishi - $episode"
    set -a mkv_command --title $title

    set output_file "Publish/[Kekkan] Tensei Akujo no Kuro Rekishi (WebRip 1080p AV1 Multi-Subs Alicia)/$title (WebRip 1080p AV1 Multi-Subs Alicia).mkv"
    set -a mkv_command --output $output_file


    set video_file "Video/$episode.mkv"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -a mkv_command --language 0:jpn --track-name 0:"Kekkan" $video_file


    set subtitle_dir "Temp/$episode.subtitles"
    if test -e $subtitle_dir
        rm -r $subtitle_dir
    end
    mkdir $subtitle_dir

    set fonts_dir "Temp/$episode.fonts"
    if test -e $fonts_dir
        rm -r $fonts_dir
    end
    mkdir $fonts_dir


    set source_s (find $RAWS_DIRECTORY -regex ".*/\[S.* - ""$episode""v2 .*\.mkv")
    if begin test -z $source_s ; or not test -e $source_s ; end
        set source_s (find $RAWS_DIRECTORY -regex ".*/\[S.* - $episode .*\.mkv")
    end
    if begin test -z $source_s ; or not test -e $source_s ; end
        set_color red ; echo "[mux] Source S not found." ; set_color normal
        return 126
    end

    set subtitle_en "$subtitle_dir/en.ass"
    mkvextract $source_s tracks 2:$subtitle_en
    mux_restyle_subtitle $subtitle_en
    set -a mkv_command --language 0:en --track-name 0:"Kekkan · SubsPlease CR" $subtitle_en

    begin cd $fonts_dir
        ffmpeg -hide_banner -y -dump_attachment:t "" -i $source_s
        rm Roboto*.ttf
        rm CONSOLA*.TTF
        prevd
    end
    cp "Misc/Lato-Bold.ttf" "Misc/Lato-BoldItalic.ttf" "$fonts_dir/"


    set source_e (find $RAWS_DIRECTORY -regex ".*/\[E.* - $episode .*\.mkv")
    if begin test -z $source_e ; or not test -e $source_e ; end
        set_color red ; echo "[mux] Source E not found." ; set_color normal
        return 126
    end

    set ar_available
    if MediaInfo $source_e | grep "Language.*Arabic" > /dev/null
        set ar_available 1
    end
    set indonesian_available
    if MediaInfo $source_e | grep "Language.*Indonesian" > /dev/null
        set indonesian_available 1
    end
    set thai_available
    if MediaInfo $source_e | grep "Language.*Thai" > /dev/null
        set thai_available 1
    end
    set chinese_available
    if MediaInfo $source_e | grep "Language.*Chinese" > /dev/null
        set chinese_available 1
    end

    set subtitle_tracks_flag "!2"

    set head 3
    set subtitle_head "$subtitle_dir/pt-BR.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head
    set -a mkv_command --language 0:pt-BR --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    set head 4
    set subtitle_head "$subtitle_dir/es-419.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head
    set -a mkv_command --language 0:es-419 --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    set head 5
    set subtitle_head "$subtitle_dir/es.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head
    set -a mkv_command --language 0:es --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    if test -n "$ar_available"
        set head 7
    else
        set head 6
    end
    set subtitle_head "$subtitle_dir/fr.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head
    set -a mkv_command --language 0:fr --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    if test -n "$ar_available"
        set head 8
    else
        set head 7
    end
    set subtitle_head "$subtitle_dir/de.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head
    set -a mkv_command --language 0:de --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    if test -n "$ar_available"
        set head 9
    else
        set head 8
    end
    set subtitle_head "$subtitle_dir/it.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head
    set -a mkv_command --language 0:it --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    if test -n "$ar_available"
        set head 10
    else
        set head 9
    end
    set subtitle_head "$subtitle_dir/ru.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle_ru $subtitle_head
    set -a mkv_command --language 0:ru --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    if test -n "$indonesian_available"
        if test -n "$ar_available"
            set head 11
        else
            set head 10
        end
        set subtitle_head "$subtitle_dir/id.ass"
        mkvextract $source_e tracks $head:$subtitle_head
        set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
        mux_restyle_subtitle $subtitle_head
        set -a mkv_command --language 0:id --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head
    end

    cp "Misc/FiraSans-Medium.ttf" "Misc/FiraSans-MediumItalic.ttf" "$fonts_dir/"
    if test -n "$ar_available"
        cp "Misc/AdobeArabic-Bold.otf" "Misc/AdobeArabic-BoldItalic.otf" "$fonts_dir/"
    end
    if test -n "$thai_available"
        cp "Misc/NotoSansThai-Bold.ttf" "$fonts_dir/"
    end

    set -a mkv_command --no-video --track-name 1:"Erai-raws CR" --subtitle-tracks $subtitle_tracks_flag --track-name 6:"Erai-raws CR" --track-name 9:"Erai-raws CR" --track-name 10:"Erai-raws CR" --track-name 11:"Erai-raws CR" --track-name 12:"Erai-raws CR" --track-name 13:"Erai-raws CR" --no-chapters --no-attachments --no-global-tags $source_e

    if test -z "$chinese_available"
        set subtitle_zh "Misc/zh-Hant.$episode.srt"
        set -a mkv_command --language 0:zh-Hant --track-name 0:"iQIYI" $subtitle_zh
    end
    
    set subtitle_zh "Misc/zh-Hans.$episode.srt"
    set -a mkv_command --language 0:zh-Hans --track-name 0:"iQIYI" $subtitle_zh


    set attach_fonts
    for f in (find $fonts_dir -type f)
        set -a mkv_command --attach-file $f
    end


    echo $mkv_command
    $mkv_command
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

    rm -rf "logs" "__pycache__" "Temp/$episode.boost.tmp" "Temp/$episode.scenes.json" "Temp/$episode.tmp" "Temp/$episode.subtitles" "Temp/$episode.fonts"

    if test -n "$clean_intermediate"
        rm -f "Intermediate/$episode.mkv" "Intermediate/$episode.mkv.ffindex"
    end
end
