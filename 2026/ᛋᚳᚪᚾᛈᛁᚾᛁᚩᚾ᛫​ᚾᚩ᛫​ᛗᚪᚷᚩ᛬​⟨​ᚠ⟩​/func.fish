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


# $argv[1]: Subtitle file
# $argv[2]: Script
function mux_restyle_subtitle
    set subtitle_file $argv[1]
    if begin test -z $subtitle_file ; or not test -e $subtitle_file ; end
        set_color red ; echo "[mux_restyle_subtitle] Subtitle file not found." ; set_color normal
        return 126
    end

    set script $argv[2]
    set fscx 100
    set fsp 0
    set margin_v_adjust 0
    if test $script = latin
        set fn PT Serif Pro DemiBold
        set fs 23
        set b 0
        set fscx 102
        set margin_v_adjust 2
    else if test $script = arabic
        set fn Bahij Nassim
        set fs 32
        set b -1
        set margin_v_adjust -4
    else if test $script = cyrillic
        set fn PT Serif Pro DemiBold
        set fs 23
        set b 0
        set fscx 102
        set margin_v_adjust 2
    else if test $script = thai
        set fn Prompt SemiBold
        set fs 25
        set b 0
        set margin_v_adjust -2
    else if test $script = cjk-Hant
        set fn Source Han Serif TC
        set fs 26
        set b -1
        set fsp 0.15
        set margin_v_adjust -1
    else if test $script = cjk-Hans
        set fn Source Han Serif SC
        set fs 26
        set b -1
        set fsp 0.15
        set margin_v_adjust -1
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
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,1,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomCenter" "Default" "Main" "Gen_Main" "TiretsDefault" "Default overlap" "Flashback" "Main_Flashback" "Overlap" "Main_Overlap" "Flashback_Overlap" "main" "flashback"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,3,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics" "Italic" "Main_Italic" "Gen_Italics" "Italique" "TiretsItalique" "Flashback Italics" "Flashback - Italics" "Internal" "Overlap Internal" "Flashback Internal" "Main_Flashback_Italic" "Flashback_Italics" "italic" "italics" "Narration" "Narratore" "Narrator"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H18D0D7EB,&H000000FF,&H3020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.10,0,2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,7,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopCenter" "Top" "Main_Top" "Gen_Main_Up" "Main - Top" "On Top" "Flashback Top" "Main_Flashback_Top" "Flashback_Top" "Overlap Top" "top" "Default - Top"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,9,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics Top" "Main_Top_Italic" "Gen_Italics_top" "DefaultItalicsTop" "Flashback Italics Top" "Italics - Top" "ItalicsTop" "Top Internal" "Italics_Top" "Internal Top"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H18D0D7EB,&H000000FF,&H3020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.10,0,8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,4,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterCenter"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,5,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04D0D7EB,&H000000FF,&H0020125C,&HA8000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.20,0,6,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
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

    set title "[Kekkan] Champignon no Majo - $episode"
    set -a mkv_command --title $title

    set output_file "Publish/[Kekkan] Champignon no Majo (WebRip 1080p AV1 Multi-Subs Alicia)/$title (WebRip 1080p AV1 Multi-Subs Alicia).mkv"
    set -a mkv_command --output $output_file


    set video_file "Video/$episode.ivf"
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

    # cp -v Misc/GenericFonts/* "$fonts_dir/"


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
    cp -v "Misc/Fonts/PTSerifPro-DemiBold.ttf" "Misc/Fonts/PTSerifPro-DemiBoldItalic.ttf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_en latin
    set -a mkv_command --language 0:en --track-name 0:"Kekkan · SubsPlease CR" $subtitle_en


    set -a mkv_command --no-video --track-name 1:"SubsPlease CR" --no-subtitles --no-chapters --no-attachments --no-global-tags $source_s


    set source_t (find $RAWS_DIRECTORY -regex ".*/C.*\.S01E$episode\..*b\.mkv")
    if begin test -z $source_t ; or not test -e $source_t ; end
        set_color red ; echo "[mux] Source T not found." ; set_color normal
        return 126
    end

    set subtitle_tracks_flag "!2"

    set head 3
    set subtitle_head "$subtitle_dir/ar.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head arabic
    cp -v "Misc/Fonts/Bahij Nassim-Bold.ttf" "$fonts_dir/"
    set -a mkv_command --language 0:ar --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set head 4
    set subtitle_head "$subtitle_dir/fr.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:fr --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set head 5
    set subtitle_head "$subtitle_dir/de.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:de --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set head 6
    set subtitle_head "$subtitle_dir/it.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:it --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set head 7
    set subtitle_head "$subtitle_dir/pt-BR.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:pt-BR --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set head 8
    set subtitle_head "$subtitle_dir/ru.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head cyrillic
    set -a mkv_command --language 0:ru --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set head 9
    set subtitle_head "$subtitle_dir/es-419.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:es-419 --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set head 10
    set subtitle_head "$subtitle_dir/es.ass"
    mkvextract $source_t tracks $head:$subtitle_head
    set subtitle_tracks_flag "$subtitle_tracks_flag,$head"
    mux_restyle_subtitle $subtitle_head latin
    set -a mkv_command --language 0:es --track-name 0:"Kekkan · ToonsHub CR" $subtitle_head

    set subtitle_head "$subtitle_dir/zh-Hant.ass"
    ffmpeg -hide_banner -i "Misc/Subtitles/zh-Hant.$episode.srt" -c:s ass $subtitle_head
    mux_restyle_subtitle $subtitle_head cjk-Hant
    set -a mkv_command --language 0:zh-Hant --track-name 0:"Kekkan · iQIYI" $subtitle_head

    set subtitle_head "$subtitle_dir/zh-Hans.ass"
    ffmpeg -hide_banner -i "Misc/Subtitles/zh-Hans.$episode.srt" -c:s ass $subtitle_head
    mux_restyle_subtitle $subtitle_head cjk-Hans
    set -a mkv_command --language 0:zh-Hans --track-name 0:"Kekkan · iQIYI" $subtitle_head


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
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    rm -rf "__pycache__" "Temp/$episode.vsmuxtools.tmp" "Temp/$episode.subtitles" "Temp/$episode.fonts"
end
