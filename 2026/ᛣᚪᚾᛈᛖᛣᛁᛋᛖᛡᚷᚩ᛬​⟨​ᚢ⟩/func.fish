# $argv[1]: Episode number "01"
function encode
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set main_encode "Main/$episode.265"
    set mini_encode "Mini/$episode.ivf"
    set mini_keyframes "Temp/$episode.cfg"

    if test -e $main_encode
        set_color red ; echo "[encode] Main encode file already exists. Skipping main encode..." ; set_color normal
    end
    if test -e $mini_encode
        set_color red ; echo "[encode] Mini encode file already exists. Skipping mini encode..." ; set_color normal
    end

    set main_parameters -o $main_encode --preset slower --crf 13.20 --bframes 16 --ref 4 --rc-lookahead 60 --subme 5 --me 3 --aq-mode 5 --aq-strength 0.45 --qcomp 0.75 --cbqpoffs -2 --crqpoffs -2 --rd 4 --psy-rd 2.0 --psy-rdoq 2.0 --tu-intra-depth 2 --tu-inter-depth 2 --rect --no-amp --no-tskip --b-intra --weightb --no-cutree --rskip 0 --deblock=-2:-2 --no-sao --no-sao-non-deblock --no-strong-intra-smoothing --no-open-gop --asm avx512 --hist-scenecut --aq-bias-strength 1.50 --aom-film-grain grain.bin --input-depth 10 --output-depth 10 --transfer 1 --chromaloc 0 --colormatrix 1 --range limited --colorprim 1 --sar 1:1 --min-luma 64 --max-luma 940 --y4m --input -
    set mini_parameters --preset 2 --crf 24.20 --lineart-psy-bias 5 --texture-psy-bias 4 --progress 2 --noise-level-thr 21000 --satd-bias 0.50 --dlf-bias-max-dlf 24,2 --dlf-bias-min-dlf 16,0 --dlf-sharpness 7 --texture-cdef-bias-max-cdef 0,0,0,0 --fgs-table grain.tbl --keyint 0 --scd 0 -c $mini_keyframes --fps-num 24000 --fps-denom 1001 --input-depth 10 --chroma-sample-position left --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0 -b $mini_encode -i -

    if begin not test -e $mini_encode; and not test -e $mini_keyframes; end
        EPISODE=$episode python mini_keyframes.py
    end

    if begin not test -e $main_encode; and not test -e $mini_encode; end
        EPISODE=$episode VSPipe filter.py -c y4m - | begin tee /dev/stderr 2>| x265 $main_parameters ; end | SvtAv1EncApp $mini_parameters
    else if not test -e $main_encode
        EPISODE=$episode VSPipe filter.py -c y4m - | x265 $main_parameters
    else if and not test -e $mini_encode
        EPISODE=$episode VSPipe filter.py -c y4m - | SvtAv1EncApp $mini_parameters
    end

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
function encode_nc
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[encode] Encoding $episode..." ; set_color normal

    set main_encode "Main/$episode.ivf"
    set mini_encode "Mini/$episode.ivf"
    set main_keyframes "Temp/$episode.cfg"

    if test -e $main_encode
        set_color red ; echo "[encode] Main encode file already exists. Skipping main encode..." ; set_color normal
    end
    if test -e $mini_encode
        set_color red ; echo "[encode] Mini encode file already exists. Skipping mini encode..." ; set_color normal
    end

    set main_parameters --preset 2 --crf 15.20 --lineart-psy-bias 5 --texture-psy-bias 4 --progress 2 --satd-bias 0.50 --fgs-table grain.tbl --keyint 0 --scd 0 -c $main_keyframes --fps-num 24000 --fps-denom 1001 --input-depth 10 --chroma-sample-position left --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0 -b $main_encode -i -
    set mini_parameters --preset 2 --crf 24.20 --lineart-psy-bias 5 --texture-psy-bias 4 --progress 2 --noise-level-thr 21000 --satd-bias 0.50 --dlf-bias-max-dlf 24,2 --dlf-bias-min-dlf 16,0 --dlf-sharpness 7 --texture-cdef-bias-max-cdef 0,0,0,0 --fgs-table grain.tbl --keyint 0 --scd 0 -c $main_keyframes --fps-num 24000 --fps-denom 1001 --input-depth 10 --chroma-sample-position left --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0 -b $mini_encode -i -

    if begin begin not test -e $main_encode; or not test -e $mini_encode; end; and not test -e $main_keyframes; end
        EPISODE=$episode python mini_keyframes.py
    end

    if not test -e $main_encode
        EPISODE=$episode VSPipe filter.py -c y4m - | SvtAv1EncApp $main_parameters
    end

    if begin not test -e $main_encode; and not test -e $mini_encode; end
        EPISODE=$episode VSPipe filter.py -c y4m - | begin tee /dev/stderr 2>| SvtAv1EncApp $main_parameters ; end | SvtAv1EncApp $mini_parameters
    else if not test -e $main_encode
        EPISODE=$episode VSPipe filter.py -c y4m - | SvtAv1EncApp $main_parameters
    else if and not test -e $mini_encode
        EPISODE=$episode VSPipe filter.py -c y4m - | SvtAv1EncApp $mini_parameters
    end

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


# $argv[1]: Subtitle file
# $argv[2]: Script
function mux_restyle_subtitle
    set subtitle_file $argv[1]
    if begin test -z $subtitle_file ; or not test -e $subtitle_file ; end
        set_color red ; echo "[mux_restyle_subtitle] Subtitle file not found." ; set_color normal
        return 126
    end

    set script $argv[2]
    set i -1
    set fscx 100
    set fsp 0
    set shad_adjust 0
    set margin_v_adjust 0
    if test $script = latin
        set fn Gandhi Sans
        set fs 24
        set b -1
        set margin_v_adjust 0
    else if test $script = latin-VI
        set fn Fira Sans Medium
        set fs 24
        set b 0
        set margin_v_adjust 0
    else if test $script = arabic
        set fn Bahij Nassim
        set fs 33
        set b 0
        set i 0
        set margin_v_adjust -3
    else if test $script = cyrillic
        set fn Fira Sans Medium
        set fs 24
        set b 0
        set margin_v_adjust 0
    else if test $script = thai
        set fn Prompt SemiBold
        set fs 26
        set b 0
        set margin_v_adjust -2
    else if test $script = cjk-Hant
        set fn Source Han Sans TC
        set fs 26
        set b -1
        set fsp 0.01
        set shad_adjust -0.50
        set margin_v_adjust 0
    else if test $script = cjk-Hans
        set fn Source Han Sans SC
        set fs 26
        set b -1
        set fsp 0.01
        set shad_adjust -0.50
        set margin_v_adjust 0
    else if test $script = cjk-JP
        set fn Source Han Sans JP
        set fs 26
        set b -1
        set fsp 0.01
        set shad_adjust -0.50
        set margin_v_adjust 0
    else
        set_color red ; echo "[mux_restyle_subtitle] Unrecognised script `$script`." ; set_color normal
        return 126
    end

    string replace --regex "^PlayResX: .*" "PlayResX: 640" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^PlayResY: .*" "PlayResY: 360" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^(PlayResY.*)" "\$1\nScript Updated By: Kekkan" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^ScaledBorderAndShadow: .*" "ScaledBorderAndShadow: yes" (cat $subtitle_file) > $subtitle_file
    or string replace --regex "^(PlayResY.*)" "\$1\nScaledBorderAndShadow: yes" (cat $subtitle_file) > $subtitle_file
    string replace --regex "^YCbCr Matrix: .*" "YCbCr Matrix: TV.709" (cat $subtitle_file) > $subtitle_file
    or string replace --regex "^(PlayResY.*)" "\$1\nYCbCr Matrix: TV.709" (cat $subtitle_file) > $subtitle_file


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
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),1,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomCenter" "Default" "Main" "Gen_Main" "TiretsDefault" "Default overlap" "Flashback" "Main_Flashback" "Overlap" "Main_Overlap" "Flashback_Overlap" "main" "main - flashback" "Font1" "Основной"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "BottomRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),3,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics" "Italic" "Main_Italic" "Gen_Italics" "Italique" "TiretsItalique" "Flashback Italics" "Flashback - Italics" "Internal" "Overlap Internal" "Flashback Internal" "Main_Flashback_Italic" "Flashback_Italics" "Narration" "Narratore" "Narrator" "main - italics" "Flashback italics" "Flashback-Italics" "flashback italics" "Курсив" "Main - Italics" "Flashback - Italics" "Flashback - Internal" "Overlap - Internal"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,$i,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),2,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),7,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopCenter" "Top" "Main_Top" "Gen_Main_Up" "Main - Top" "On Top" "Flashback Top" "Main_Flashback_Top" "Flashback_Top" "Overlap Top" "Default - Top" "main - top" "main - flashback - top" "Flashback top" "Flashback Overlap top" "Flashback-Top" "main - shifted" "flashbacktop" "Основной-сверху" "Flashback - Top" "Flashback - Internal TOP" "Overlap - TOP"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "TopRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),9,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "Italics Top" "Main_Top_Italic" "Gen_Italics_top" "DefaultItalicsTop" "Flashback Italics Top" "Italics - Top" "ItalicsTop" "Top Internal" "Italics_Top" "Internal Top" "main - italics top" "Italics-Top" "Main_Italic_Top" "flashbackitalicstop" "italicstop" "Курсив-сверху" "Flashback italics top" "Italics top" "Main - Top \\+ Italics" "Flashback - Top \\+ Italics" "Overlap - Internal - TOP"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,$i,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),8,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterLeft"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),4,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterCenter"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),5,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
    end
    for style in "CenterRight"
        string replace --regex "^Style: $style,.*" "Style: $style,$fn,$fs,&H04F9F0F6,&H000000FF,&H184C2834,&HBF3D223B,$b,0,0,0,$fscx,100,$fsp,0,1,1.3,$(math 0.5 + $shad_adjust),6,40,40,$(math 20 + $margin_v_adjust),1" (cat $subtitle_file) > $subtitle_file
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


    set sub_langs_file "Publish/Subs.txt"


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


    set source_t (python information.py source_web $episode)
    if begin test -z $source_t ; or not test -e $source_t ; end
        set_color red ; echo "[mux] Source T not found." ; set_color normal
        return 126
    end

    set head 2
    set subtitle_file "$subtitle_dir/en.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    cp -v "Misc/Fonts/GandhiSans-Bold.otf" "Misc/Fonts/GandhiSans-BoldItalic.otf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_file latin
    echo en > $sub_langs_file
    set -g subs_mkv_command --language 0:en --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set subtitle_head "$subtitle_dir/ja.ass"
    ffmpeg -hide_banner -i "Misc/Subtitles/ja.$episode.srt" -c:s ass $subtitle_head
    python Misc/fix_gap.py --output $subtitle_head $subtitle_head
    cp -v "Misc/Fonts/SourceHanSansJP-Bold.otf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_head cjk-JP
    echo ja >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:ja --sync 0:-1001 --track-name 0:"Kekkan · NF" $subtitle_head

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/ar.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    cp -v "Misc/Fonts/Bahij Nassim-Bold.ttf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_file arabic
    echo ar >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:ar --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set subtitle_head "$subtitle_dir/zh-Hant.ass"
    ffmpeg -hide_banner -i "Misc/Subtitles/zh-Hant.$episode.srt" -c:s ass $subtitle_head
    mux_restyle_subtitle $subtitle_head cjk-Hant
    echo zh-Hant >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:zh-Hant --track-name 0:"Kekkan · KKTV" $subtitle_head

    set subtitle_head "$subtitle_dir/zh-Hans.ass"
    ffmpeg -hide_banner -i "Misc/Subtitles/zh-Hans.$episode.srt" -c:s ass $subtitle_head
    mux_restyle_subtitle $subtitle_head cjk-Hans
    echo zh-Hans >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:zh-Hans --track-name 0:"Kekkan · KKTV" $subtitle_head

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/fr.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo fr >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:fr --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/de.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo de >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:de --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/id.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo id >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:id --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/it.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo it >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:it --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/ms.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo ms >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:ms --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/pt-BR.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo pt-BR >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:pt-BR --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/ru.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    cp -v "Misc/Fonts/FiraSans-Medium.ttf" "Misc/Fonts/FiraSans-MediumItalic.ttf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_file cyrillic
    echo ru >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:ru --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/es-419.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    python Misc/fix_gap.py --output $subtitle_file $subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo es-419 >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:es-419 --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/es-ES.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    python Misc/fix_gap.py --output $subtitle_file $subtitle_file
    mux_restyle_subtitle $subtitle_file latin
    echo es-ES >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:es-ES --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/th.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    cp -v "Misc/Fonts/Prompt-SemiBold.ttf" "$fonts_dir/"
    mux_restyle_subtitle $subtitle_file thai
    echo th >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:th --track-name 0:"Kekkan · ToonsHub" $subtitle_file

    set head (math $head + 1)
    set subtitle_file "$subtitle_dir/vi.ass"
    mkvextract $source_t tracks $head:$subtitle_file
    mux_restyle_subtitle $subtitle_file latin-VI
    echo vi >> $sub_langs_file
    set -g -a subs_mkv_command --language 0:vi --track-name 0:"Kekkan · ToonsHub" $subtitle_file


    set attach_fonts
    for f in (find $fonts_dir -type f)
        set -g -a subs_mkv_command --attach-file $f
    end


    set -g main_mkv_command mkvmerge --deterministic 0
    set -g mini_mkv_command mkvmerge --deterministic 0

    set title "[Kekkan] Kanpekiseijo - $episode"
    set -g -a main_mkv_command --title $title
    set -g -a mini_mkv_command --title $title

    set chapters_file "Misc/Chapters/$episode.txt"
    set -g -a main_mkv_command --chapters $chapters_file
    set -g -a mini_mkv_command --chapters $chapters_file


    set main_output_file "Publish/[Kekkan] Kanpekiseijo (BD 1080p HEVC FLAC Multi-Subs)/$title (BD 1080p HEVC FLAC Multi-Subs).mkv"
    set mini_output_file "Publish/[Kekkan] Kanpekiseijo (BD 1080p AV1 Multi-Subs)/$title (BD 1080p AV1 Multi-Subs).mkv"
    set -g -a main_mkv_command --output $main_output_file
    set -g -a mini_mkv_command --output $mini_output_file


    set main_video_file "Main/$episode.265"
    if not test -e $main_video_file
        set_color red ; echo "[mux] Main video file not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Kekkan" $main_video_file

    set mini_video_file "Mini/$episode.ivf"
    if not test -e $mini_video_file
        set_color red ; echo "[mux] Mini video file not found." ; set_color normal
        return 126
    end
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Kekkan" $mini_video_file

    
    set main_audio_file "Temp/$episode.flac"
    set main_audio_file_win "Temp\\$episode.flac"
    if not test -e $main_audio_file
        eac3to (python information.py source_bd $episode) 2: $main_audio_file_win -log=/dev/null
        or return $status
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Kekkan" $main_audio_file

    set mini_audio_file "Temp/$episode.opus"
    if not test -e $mini_audio_file
        opusenc $main_audio_file $mini_audio_file --bitrate 160
        or return $status
    end
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Kekkan" $mini_audio_file


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

    set title "[Kekkan] Kanpekiseijo - $episode"
    set -g -a main_mkv_command --title $title


    set main_output_file "Publish/[Kekkan] Kanpekiseijo (BD 1080p HEVC FLAC Multi-Subs)/$title (BD 1080p AV1 FLAC).mkv"
    set mini_output_file "Publish/[Kekkan] Kanpekiseijo (BD 1080p AV1 Multi-Subs)/$title (BD 1080p AV1 FLAC).mkv"
    set -g -a main_mkv_command --output $main_output_file
    set -g -a mini_mkv_command --output $mini_output_file


    set main_video_file "Main/$episode.ivf"
    if not test -e $main_video_file
        set_color red ; echo "[mux] Main video file not found." ; set_color normal
        return 126
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Kekkan" $main_video_file

    set mini_video_file "Mini/$episode.ivf"
    if not test -e $mini_video_file
        set_color red ; echo "[mux] Mini video file not found." ; set_color normal
        return 126
    end
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Kekkan" $mini_video_file

    
    set main_audio_file "Temp/$episode.flac"
    set main_audio_file_win "Temp\\$episode.flac"
    if not test -e $main_audio_file
        eac3to (python information.py source_bd $episode) 2: $main_audio_file_win -log=/dev/null
        or return $status
    end
    set -g -a main_mkv_command --language 0:ja --track-name 0:"Kekkan" $main_audio_file
    set -g -a mini_mkv_command --language 0:ja --track-name 0:"Kekkan" $main_audio_file


    echo $main_mkv_command
    $main_mkv_command
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

    rm -rf "__pycache__" "Temp/$episode.cfg" "Temp/$episode.flac" "Temp/$episode.opus" "Temp/$episode.subtitles" "Temp/$episode.fonts"
end
