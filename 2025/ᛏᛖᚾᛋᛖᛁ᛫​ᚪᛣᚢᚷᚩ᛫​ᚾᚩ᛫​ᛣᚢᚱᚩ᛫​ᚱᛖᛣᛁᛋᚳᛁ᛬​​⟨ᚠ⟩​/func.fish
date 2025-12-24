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
# $argv[2]: Script
function mux_restyle_subtitle
    set subtitle_file $argv[1]
    if begin test -z $subtitle_file ; or not test -e $subtitle_file ; end
        set_color red ; echo "[mux_restyle_subtitle] Subtitle file not found." ; set_color normal
        return 126
    end

    set script $argv[2]
    set shad_adjust 0
    set margin_v_adjust 0
    if test $script = latin
        set fn Lato
        set fs 23
        set b -1
    else if test $script = arabic
        set fn Bahij Nassim
        set fs 32
        set b 0
        set shad_adjust -0.40
        set margin_v_adjust -6
    else if test $script = cyrillic
        set fn Fira Sans Medium
        set fs 22
        set b 0
    else if test $script = thai
        set fn Prompt SemiBold
        set fs 25
        set b 0
        set shad_adjust -0.40
        set margin_v_adjust -2
    else if test $script = cjk-Hant
        set fn Source Han Sans TC
        set fs 26
        set b -1
        set shad_adjust -0.40
    else if test $script = cjk-Hans
        set fn Source Han Sans SC
        set fs 26
        set b -1
        set shad_adjust -0.40
    else
        set_color red ; echo "[mux_restyle_subtitle] Unrecognised script." ; set_color normal
        return 126
    end
    
    string replace --regex "^PlayResX: .*" "PlayResX: 640" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^PlayResY: .*" "PlayResY: 360" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^(PlayResY.*)" "\$1\nScript Updated By: Kekkan" (cat $subtitle_file) > $subtitle_file
    
    if test $script = arabic
        string replace --regex "^WrapStyle: .*" "WrapStyle: 1" (cat $subtitle_file) > $subtitle_file
        or string replace --regex "^(PlayResY.*)" "\$1\nWrapStyle: 1" (cat $subtitle_file) > $subtitle_file
        string replace --all --regex "\\\\i[01]" "" (cat $subtitle_file) > $subtitle_file
        string replace --all --regex "{}" "" (cat $subtitle_file) > $subtitle_file
        string replace --regex "(Dialogue: (?:[^,]*,){9})([^{].*?[^\"–])\\\\N([^{].*)" "\$1‪\$3 ‪\$2" (cat $subtitle_file) > $subtitle_file
    end

    for style in "BottomLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),1,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomCenter" "Default" "Main" "Gen_Main" "Narration" "Narratore" "TiretsDefault" "Default overlap" "Flashback" "Main_Flashback"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),3,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics" "Italic" "Main_Italic" "Gen_Italics" "Italique" "TiretsItalique" "Flashback Italics" "Flashback - Italics" "Main_Flashback_Italic"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,-1,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),7,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopCenter" "Top" "Main_Top" "Gen_Main_Up" "Main - Top" "On Top" "Flashback Top" "Main_Flashback_Top"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),9,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics Top" "Main_Top_Italic" "Gen_Italics_top" "DefaultItalicsTop" "Flashback Italics Top" "Italics - Top" "ItalicsTop"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,-1,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),4,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterCenter"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),5,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H00FFFFFF,&H000000FF,&H00000028,&HA8000000,$b,0,0,0,100,100,0,0,1,1.10,$(math 0.40 + $shad_adjust),6,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
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

    cp -v Misc/GenericFonts/* "$fonts_dir/"


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
    cp -v "Misc/Fonts/Lato-Bold.ttf" "Misc/Fonts/Lato-BoldItalic.ttf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_en latin
    set -a mkv_command --language 0:en --track-name 0:"Kekkan · SubsPlease CR" $subtitle_en


    set source_e (find $RAWS_DIRECTORY -regex ".*/\[E.* - $episode .*\.mkv")
    if begin test -z $source_e ; or not test -e $source_e ; end
        set_color red ; echo "[mux] Source E not found." ; set_color normal
        return 126
    end

    set arabic_available
    if MediaInfo $source_e | grep "Language.*Arabic" > /dev/null
        set arabic_available 1
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
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:pt-BR --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    set head 4
    set subtitle_head "$subtitle_dir/es-419.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:es-419 --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    set head 5
    set subtitle_head "$subtitle_dir/es.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:es --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    if test -n "$arabic_available"
        set head 6
        set subtitle_head "$subtitle_dir/ar.ass"
        mkvextract $source_e tracks $head:$subtitle_head
        set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
        cp -v "Misc/Fonts/Bahij Nassim-Bold.ttf" "$fonts_dir/"
        mux_restyle_subtitle $subtitle_head arabic
        set -a mkv_command --language 0:ar --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head
    end

    set head (math 6 + (count $arabic_available))
    set subtitle_head "$subtitle_dir/fr.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:fr --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    set head (math 7 + (count $arabic_available))
    set subtitle_head "$subtitle_dir/de.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:de --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    set head (math 8 + (count $arabic_available))
    set subtitle_head "$subtitle_dir/it.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:it --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    set head (math 9 + (count $arabic_available))
    set subtitle_head "$subtitle_dir/ru.ass"
    mkvextract $source_e tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    cp -v "Misc/Fonts/FiraSans-Medium.ttf" "Misc/Fonts/FiraSans-MediumItalic.ttf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_head cyrillic
    set -a mkv_command --language 0:ru --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head

    if test -n "$indonesian_available"
        set head (math 10 + (count $arabic_available))
        set subtitle_head "$subtitle_dir/id.ass"
        mkvextract $source_e tracks $head:$subtitle_head
        set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
        mux_restyle_subtitle $subtitle_head latin
        set -a mkv_command --language 0:id --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head
    end

    if test -n "$thai_available"
        set head (math 10 + (count $arabic_available $indonesian_available))
        set subtitle_head "$subtitle_dir/th.ass"
        mkvextract $source_e tracks $head:$subtitle_head
        set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
        cp -v "Misc/Fonts/Prompt-SemiBold.ttf" "$fonts_dir/"
        mux_restyle_subtitle $subtitle_head thai
        set -a mkv_command --language 0:th --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head
    end
    
    if test -n "$chinese_available"
        set head (math 10 + (count $arabic_available $indonesian_available $thai_available))
        set subtitle_head "$subtitle_dir/zh-Hant.ass"
        mkvextract $source_e tracks $head:$subtitle_head
        set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
        mux_restyle_subtitle $subtitle_head cjk-Hant
        set -a mkv_command --language 0:zh-Hant --track-name 0:"Kekkan · Erai-raws CR" $subtitle_head
    else
        set subtitle_head "$subtitle_dir/zh-Hant.ass"
        ffmpeg -hide_banner -i "Misc/Subtitles/zh-Hant.$episode.srt" -c:s ass $subtitle_head
        mux_restyle_subtitle $subtitle_head cjk-Hant
        set -a mkv_command --language 0:zh-Hant --track-name 0:"Kekkan · iQIYI" $subtitle_head
    end
    
    set subtitle_head "$subtitle_dir/zh-Hans.ass"
    ffmpeg -hide_banner -i "Misc/Subtitles/zh-Hans.$episode.srt" -c:s ass $subtitle_head
    mux_restyle_subtitle $subtitle_head cjk-Hans
    set -a mkv_command --language 0:zh-Hans --track-name 0:"Kekkan · iQIYI" $subtitle_head


    set -a mkv_command --no-video --track-name 1:"Erai-raws CR" --subtitle-tracks $subtitle_tracks_flag --no-chapters --no-attachments --no-global-tags $source_e


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
