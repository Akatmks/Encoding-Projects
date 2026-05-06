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

    set main_parameters -o $main_encode --preset slower --crf 11.50 --bframes 16 --ref 4 --rc-lookahead 60 --subme 5 --me 3 --aq-mode 5 --aq-strength 0.6 --qcomp 0.75 --cbqpoffs -2 --crqpoffs -2 --rd 4 --psy-rd 2.0 --psy-rdoq 2.0 --tu-intra-depth 2 --tu-inter-depth 2 --rect --no-amp --no-tskip --b-intra --weightb --no-cutree --rskip 0 --deblock=-2:-2 --no-sao --no-sao-non-deblock --no-strong-intra-smoothing --no-open-gop --asm avx512 --hist-scenecut --aom-film-grain grain.bin --input-depth 10 --output-depth 10 --transfer 1 --chromaloc 0 --colormatrix 1 --range limited --colorprim 1 --sar 1:1 --min-luma 64 --max-luma 940 --y4m --input -
    set mini_parameters --preset 2 --crf 27.50 --lineart-psy-bias 4 --texture-psy-bias 5 --progress 2 --noise-level-thr 21000 --hierarchical-levels 4 --balancing-noise-level-q-bias 1.05 --satd-bias 0.50 --dlf-bias-max-dlf 24,4 --dlf-bias-min-dlf 16,0 --dlf-sharpness 7 --cdef-bias-damping-offset 2 --texture-cdef-bias-max-cdef 0,0,0,0 --fgs-table grain.tbl --keyint 0 --scd 0 -c $mini_keyframes --fps-num 24000 --fps-denom 1001 --input-depth 10 --chroma-sample-position left --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0 -b $mini_encode -i -

    if begin not test -e $mini_encode; and not test -e $mini_keyframes; end
        EPISODE=episode python mini_keyframes.py
    end

    if begin not test -e $main_encode; and not test -e $mini_encode; end
        EPISODE=episode VSPipe encode.py -c y4m - | begin tee /dev/stderr 2>| x265 $main_parameters ; end | SvtAv1EncApp $mini_parameters
    else if not test -e $main_encode
        EPISODE=episode VSPipe encode.py -c y4m - | x265 $main_parameters
    else if and not test -e $mini_encode
        EPISODE=episode VSPipe encode.py -c y4m - | SvtAv1EncApp $mini_parameters
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
function clean
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[clean] Episode number not provided." ; set_color normal
        return 126
    end

    rm -rf "__pycache__" "Temp/$episode.cfg"
end
