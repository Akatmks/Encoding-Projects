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

    # python Misc/fix_gap.py --output $subtitle_file $subtitle_file

    set script $argv[2]
    set i -1
    set fscx 100
    set fsp 0
    set margin_v_adjust 0
    if test $script = latin
        set fn SN Pro SemiBold
        set fs 26
        set b 0
        set margin_v_adjust -6
    else if test $script = arabic
        set fn Bahij Nassim
        set fs 33
        set b 0
        set i 0
        set margin_v_adjust -8
    else if test $script = cyrillic
        set fn SN Pro SemiBold
        set fs 26
        set b 0
        set margin_v_adjust -6
    else if test $script = thai
        set fn Prompt SemiBold
        set fs 26
        set b 0
        set margin_v_adjust -3
    else if test $script = cjk-Hant
        set fn Source Han Sans TC
        set fs 26
        set b -1
        set fsp 0.01
        set margin_v_adjust 0
    else if test $script = cjk-Hans
        set fn Source Han Sans SC
        set fs 26
        set b -1
        set fsp 0.01
        set margin_v_adjust 0
    else
        set_color red ; echo "[mux_restyle_subtitle] Unrecognised script `$script`." ; set_color normal
        return 126
    end

    string replace --regex "^PlayResX: .*" "PlayResX: 640" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^PlayResY: .*" "PlayResY: 360" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^(PlayResY.*)" "\$1\nScript Updated By: Himejoshi" (cat $subtitle_file) > $subtitle_file

    if test $script = arabic
        string replace --regex "^WrapStyle: .*" "WrapStyle: 1" (cat $subtitle_file) > $subtitle_file
        or string replace --regex "^(PlayResY.*)" "\$1\nWrapStyle: 1" (cat $subtitle_file) > $subtitle_file
        string replace --all --regex "\\\\i[01]" "" (cat $subtitle_file) > $subtitle_file
        string replace --all --regex "{}" "" (cat $subtitle_file) > $subtitle_file
        string replace --regex "(Dialogue: (?:[^,]*,){9})([^{].*?[^\"–])\\\\N([^{].*)" "\$1‪\$3 ‪\$2" (cat $subtitle_file) > $subtitle_file
    end

    if begin string match --quiet --regex "^Dialogue: [0-9:\.,]+?,Default," (cat $subtitle_file)
        and not string match --quiet --regex "^Style: Default," (cat $subtitle_file)
    end
        string replace --regex "(Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding)" "\$1\nStyle: Default," (cat $subtitle_file) > $subtitle_file
    end
    if string match --quiet --regex "^Dialogue: [0-9:\.,]+?,Font1," (cat $subtitle_file)
        string replace --regex "(Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding)" "\$1\nStyle: Font1," (cat $subtitle_file) > $subtitle_file
    end

    for style in "BottomLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,1,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomCenter" "Default" "Main" "Gen_Main" "TiretsDefault" "Default overlap" "Flashback" "Main_Flashback" "Overlap" "Main_Overlap" "Flashback_Overlap" "main" "flashback" "main - flashback" "Font1" "flashback" "Основной" "Flashback - Internal" "BD DX"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,3,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics" "Italic" "Main_Italic" "Gen_Italics" "Italique" "TiretsItalique" "Flashback Italics" "Flashback - Italics" "Internal" "Overlap Internal" "Flashback Internal" "Main_Flashback_Italic" "Flashback_Italics" "italic" "italics" "Narration" "Narratore" "Narrator" "main - italics" "Flashback italics" "Flashback-Italics" "flashback italics" "Курсив"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,$i,0,0,$fscx,100,$fsp,0,1,1.15,0,2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,7,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopCenter" "Top" "Main_Top" "Gen_Main_Up" "Main - Top" "On Top" "Flashback Top" "Main_Flashback_Top" "Flashback_Top" "Overlap Top" "top" "Default - Top" "main - top" "main - flashback - top" "Flashback top" "Flashback Overlap top" "Flashback-Top" "main - shifted" "flashbacktop" "Основной-сверху" "Flashback - Top" "overlaptop" "Overlap top" "Default Top" "Flashback - Internal Top"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,9,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics Top" "Main_Top_Italic" "Gen_Italics_top" "DefaultItalicsTop" "Flashback Italics Top" "Italics - Top" "ItalicsTop" "Top Internal" "Italics_Top" "Internal Top" "main - italics top" "Italics-Top" "Main_Italic_Top" "flashbackitalicstop" "italicstop" "Курсив-сверху" "Flashback italics top" "Italics top" "Overlap Internal Top"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,$i,0,0,$fscx,100,$fsp,0,1,1.15,0,8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,4,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterCenter"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,5,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$fsp,0,1,1.15,0,6,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
end


# $argv[1]: Subtitle file
# $argv[2]: Script
function mux_restyle_subtitle_1080p
    set subtitle_file $argv[1]
    if begin test -z $subtitle_file ; or not test -e $subtitle_file ; end
        set_color red ; echo "[mux_restyle_subtitle] Subtitle file not found." ; set_color normal
        return 126
    end

    # python Misc/fix_gap.py --output $subtitle_file $subtitle_file

    set script $argv[2]
    set i -1
    set fscx 100
    set fsp 0
    set margin_v_adjust 0
    if test $script = latin
        set fn SN Pro SemiBold
        set fs 26
        set b 0
        set margin_v_adjust -6
    else if test $script = arabic
        set fn Bahij Nassim
        set fs 33
        set b 0
        set i 0
        set margin_v_adjust -9
    else if test $script = cyrillic
        set fn SN Pro SemiBold
        set fs 26
        set b 0
        set margin_v_adjust -6
    else if test $script = thai
        set fn Prompt SemiBold
        set fs 26
        set b 0
        set margin_v_adjust -3
    else if test $script = cjk-Hant
        set fn Source Han Sans TC
        set fs 26
        set b -1
        set fsp 0.01
        set margin_v_adjust 0
    else if test $script = cjk-Hans
        set fn Source Han Sans SC
        set fs 26
        set b -1
        set fsp 0.01
        set margin_v_adjust 0
    else
        set_color red ; echo "[mux_restyle_subtitle] Unrecognised script `$script`." ; set_color normal
        return 126
    end

    string replace --regex "^PlayResX: .*" "PlayResX: 1920" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^PlayResY: .*" "PlayResY: 1080" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^LayoutResX: .*" "LayoutResX: 1920" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^LayoutResY: .*" "LayoutResY: 1080" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^(LayoutResY.*)" "\$1\nScript Updated By: Himejoshi" (cat $subtitle_file) > $subtitle_file

    if test $script = arabic
        string replace --regex "^WrapStyle: .*" "WrapStyle: 1" (cat $subtitle_file) > $subtitle_file
        or string replace --regex "^(PlayResY.*)" "\$1\nWrapStyle: 1" (cat $subtitle_file) > $subtitle_file
        string replace --all --regex "\\\\i[01]" "" (cat $subtitle_file) > $subtitle_file
        string replace --all --regex "{}" "" (cat $subtitle_file) > $subtitle_file
        string replace --regex "(Dialogue: (?:[^,]*,){9})([^{].*?[^\"–])\\\\N([^{].*)" "\$1‪\$3 ‪\$2" (cat $subtitle_file) > $subtitle_file
    end

    if begin string match --quiet --regex "^Dialogue: [0-9:\.,]+?,Default," (cat $subtitle_file)
        and not string match --quiet --regex "^Style: Default," (cat $subtitle_file)
    end
        string replace --regex "(Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding)" "\$1\nStyle: Default," (cat $subtitle_file) > $subtitle_file
    end
    if string match --quiet --regex "^Dialogue: [0-9:\.,]+?,Font1," (cat $subtitle_file)
        string replace --regex "(Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding)" "\$1\nStyle: Font1," (cat $subtitle_file) > $subtitle_file
    end

    for style in "BottomLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,1,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomCenter" "Default" "Main" "Gen_Main" "TiretsDefault" "Default overlap" "Flashback" "Main_Flashback" "Overlap" "Main_Overlap" "Flashback_Overlap" "main" "flashback" "main - flashback" "Font1" "flashback" "Основной" "Flashback - Internal" "BD DX"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,2,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,3,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics" "Italic" "Main_Italic" "Gen_Italics" "Italique" "TiretsItalique" "Flashback Italics" "Flashback - Italics" "Internal" "Overlap Internal" "Flashback Internal" "Main_Flashback_Italic" "Flashback_Italics" "italic" "italics" "Narration" "Narratore" "Narrator" "main - italics" "Flashback italics" "Flashback-Italics" "flashback italics" "Курсив"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,$i,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,2,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,7,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopCenter" "Top" "Main_Top" "Gen_Main_Up" "Main - Top" "On Top" "Flashback Top" "Main_Flashback_Top" "Flashback_Top" "Overlap Top" "top" "Default - Top" "main - top" "main - flashback - top" "Flashback top" "Flashback Overlap top" "Flashback-Top" "main - shifted" "flashbacktop" "Основной-сверху" "Flashback - Top" "overlaptop" "Overlap top" "Default Top" "Flashback - Internal Top"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,8,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,9,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics Top" "Main_Top_Italic" "Gen_Italics_top" "DefaultItalicsTop" "Flashback Italics Top" "Italics - Top" "ItalicsTop" "Top Internal" "Italics_Top" "Internal Top" "main - italics top" "Italics-Top" "Main_Italic_Top" "flashbackitalicstop" "italicstop" "Курсив-сверху" "Flashback italics top" "Italics top" "Overlap Internal Top"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,$i,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,8,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,4,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterCenter"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,5,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$(math $fs \* 3),&H04FFFFFF,&H000000FF,&H4048262E,&HBF000000,$b,0,0,0,$fscx,100,$(math $fsp \* 3),0,1,3.45,0,6,120,120,$(math $(math 20 + $margin_v_adjust) \* 3),1" (cat $subtitle_file) > $subtitle_file
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


    set sub_langs_file "Publish/Info/osubs.$episode.txt"

    set -g mkv_command mkvmerge --deterministic 0

    set title "☆ NEEDY GIRL OVERDOSE ☆ S01E$episode [Himejoshi]"
    set -g -a mkv_command --title $title

    EPISODE=$episode python chapters.py
    set chapters_file "Misc/Chapters/$episode.txt"
    set -g -a mkv_command --chapters $chapters_file

    set output_file "Publish/[Himejoshi] NEEDY GIRL OVERDOSE (WEB 1080p AV1)/[Himejoshi] NEEDY GIRL OVERDOSE - S01E$episode (WEB 1080p AV1).mkv"
    set -g -a mkv_command --output $output_file


    set video_file "Video/$episode.ivf"
    if not test -e $video_file
        set_color red ; echo "[mux] Video file not found." ; set_color normal
        return 126
    end
    set -g -a mkv_command --language 0:ja --track-name 0:"Himejoshi" $video_file


    set source_t (find $RAWS_DIRECTORY -regex ".*/N.*\.S01E$episode\..*\.JPN\..*b\.mkv")
    if begin test -z $source_t ; or not test -e $source_t ; end
        set_color red ; echo "[mux] Source T not found." ; set_color normal
        return 126
    end
    set -g -a mkv_command --no-video --language 1:ja --track-name 1:"ToonsHub" --no-subtitles --no-chapters --no-attachments --no-global-tags $source_t


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


    set source_u (find $RAWS_DIRECTORY -regex ".*/\[Un......\].* - S01E$episode.*\.mkv")
    if begin test -z $source_u ; or not test -e $source_u ; end
        set_color red ; echo "[mux] Source U not found." ; set_color normal
        return 126
    end

    set source_g (find $RAWS_DIRECTORY -regex ".*/\[St.... ........\].* \[$episode\].*\.mkv")
    if begin test -z $source_g ; or not test -e $source_g ; end
        set_color red ; echo "[mux] Source G not found." ; set_color normal
        return 126
    end


    set subtitle_file "$subtitle_dir/G.zh-Hans.ass"
    mkvextract $source_g tracks 2:$subtitle_file
    set -g -a mkv_command --language 0:zh-Hans --track-name 0:"绿茶字幕组" $subtitle_file
    set subtitle_file "$subtitle_dir/G.zh-Hant.ass"
    mkvextract $source_g tracks 3:$subtitle_file
    set -g -a mkv_command --language 0:zh-Hant --track-name 0:"綠茶字幕組" $subtitle_file
    begin cd $fonts_dir
        mkvextract $source_g attachments (seq 1 75)
        for f in (find . -type f)
            if string match --quiet --regex " " $f
                mv $f (string replace --all --regex " " "-" $f)
            end
        end
        prevd
    end


    set subtitle_file "$subtitle_dir/U.en.ass"
    mkvextract $source_u tracks 2:$subtitle_file
    cp -v "Misc/Fonts/SNPro-SemiBold.ttf" "Misc/Fonts/SNPro-SemiBoldItalic.ttf" "$fonts_dir/"
    mux_restyle_subtitle_1080p $subtitle_file latin
    set -g -a mkv_command --language 0:en --track-name 0:"Himejoshi · Un----ed" $subtitle_file


    set head 2
    set subtitle_file "$subtitle_dir/en.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo en > $sub_langs_file
    set -g -a mkv_command --language 0:en --track-name 0:"Himejoshi · ToonsHub" $subtitle_file


    if MediaInfo --Language=raw $source_t | grep "Language/String *: ar" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/ar.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        cp -v "Misc/Fonts/Bahij-Nassim-Bold.ttf" "$fonts_dir/"
        mux_restyle_subtitle $subtitle_file arabic
        echo ar >> $sub_langs_file
        set -g -a mkv_command --language 0:ar --track-name 0:"Himejoshi · ToonsHub" $subtitle_file
    end

    if MediaInfo --Language=raw $source_t | grep "Language/String *: fr" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/fr.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        python Misc/fix_gap.py --output $subtitle_file $subtitle_file
        mux_restyle_subtitle $subtitle_file latin
        echo fr >> $sub_langs_file
        set -g -a mkv_command --language 0:fr --track-name 0:"Himejoshi · ToonsHub" $subtitle_file
    end

    if MediaInfo --Language=raw $source_t | grep "Language/String *: de" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/de.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        mux_restyle_subtitle $subtitle_file latin
        echo de >> $sub_langs_file
        set -g -a mkv_command --language 0:de --track-name 0:"Himejoshi · ToonsHub" $subtitle_file
    end
    
    if MediaInfo --Language=raw $source_t | grep "Language/String *: it" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/it.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        mux_restyle_subtitle $subtitle_file latin
        echo it >> $sub_langs_file
        set -g -a mkv_command --language 0:it --track-name 0:"Himejoshi · ToonsHub" $subtitle_file
    end

    if MediaInfo --Language=raw $source_t | grep "Language/String *: pt (BR)" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/pt-BR.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        python Misc/fix_gap.py --output $subtitle_file $subtitle_file
        mux_restyle_subtitle $subtitle_file latin
        echo pt-BR >> $sub_langs_file
        set -g -a mkv_command --language 0:pt-BR --track-name 0:"Himejoshi · ToonsHub" $subtitle_file
    end

    if MediaInfo --Language=raw $source_t | grep "Language/String *: ru" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/ru.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        mux_restyle_subtitle $subtitle_file cyrillic
        echo ru >> $sub_langs_file
        set -g -a mkv_command --language 0:ru --track-name 0:"Himejoshi · ToonsHub" $subtitle_file

        if test $episode = 02
            string replace --regex ",0:24:40.04," ",0:23:40.04," (cat $subtitle_file) > $subtitle_file
        end 
    end

    if MediaInfo --Language=raw $source_t | grep "Language/String *: es (419)" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/es-419.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        python Misc/fix_gap.py --output $subtitle_file $subtitle_file
        mux_restyle_subtitle $subtitle_file latin
        echo es-419 >> $sub_langs_file
        set -g -a mkv_command --language 0:es-419 --track-name 0:"Himejoshi · ToonsHub" $subtitle_file
    end

    if MediaInfo --Language=raw $source_t | grep "Language/String *: es (ES)" > /dev/null
        set head (math $head + 1)
        set subtitle_file "$subtitle_dir/es-ES.ass"
        mkvextract $source_t tracks $head:$subtitle_file
        python Misc/fix_gap.py --output $subtitle_file $subtitle_file
        mux_restyle_subtitle $subtitle_file latin
        echo es-ES >> $sub_langs_file
        set -g -a mkv_command --language 0:es-ES --track-name 0:"Himejoshi · ToonsHub" $subtitle_file
    end


    set attach_fonts
    for f in (find $fonts_dir -type f)
        set -g -a mkv_command --attach-file $f
    end


    echo $mkv_command
    $mkv_command
    or return $status
    if not test -e $output_file
        set_color red ; echo "[mux] Output file missing. Exiting..." ; set_color normal
        return 126
    end


    set output_torrent_file "Publish/Torrents/[Himejoshi] NEEDY GIRL OVERDOSE - S01E$episode (WEB 1080p AV1).mkv.torrent"
    mktorrent -vf -a http://nyaa.tracker.wf:7777/announce -a https://tracker.nekobt.to/api/tracker/public/announce -a udp://tracker.opentrackr.org:1337/announce -a udp://open.stealth.si:80/announce -a udp://tracker.torrent.eu.org:451/announce -a udp://exodus.desync.com:6969/announce -o $output_torrent_file $output_file
    or return $status
    if not test -e $output_torrent_file
        set_color red ; echo "[mux] Output torrent file missing. Exiting..." ; set_color normal
        return 126
    end
end


function publish
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[publish] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[publish] Publishing $episode..." ; set_color normal

    EPISODE=$episode python Publish/publish.py
    or return $status
end


# $argv[1]: Episode number "01"
function clean
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    set log_files log*.txt
    rm -rf "__pycache__" $log_files "Temp/$episode.vsmuxtools.tmp" "Temp/$episode.subtitles" "Temp/$episode.fonts"
end
