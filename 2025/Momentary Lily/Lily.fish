#!/usr/bin/env fish

# $argv[1]: Episode number "01"
function prepare
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[prepare] Episode number not provided." ; set_color normal
        return 126
    end

    set prefix ..

    set source_file (find $prefix -regex "$prefix/\[SubsPlease\] Momentary Lily - $episode (1080p) \[[0-9A-F]+\].mkv")
    if not test -e $source_file
        set_color red ; echo "[prepare] Source file not found." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[prepare] Preparing Lily episode $episode..." ; set_color normal
    
    set temp_dir "$prefix/Lily $episode.prepare.tmp"
    set prezone_scenes_file "$prefix/Lily $episode.prezone.scenes.json"
    if test -e $temp_dir
        rm -r $temp_dir
    end
    if not test -e $prezone_scenes_file
        av1an -y --max-tries 10 --temp $temp_dir --verbose --log-level debug -i $source_file --sc-only --scenes $prezone_scenes_file --split-method av-scenechange --sc-method standard --extra-split 360 --min-scene-len 6
        or return $status
    end
    if not test -e $prezone_scenes_file
        set_color red ; echo "[prepare] Generated prezone scenes file missing. Exiting..." ; set_color normal
        return 126
    end

    set keyframes_file "$prefix/Lily $episode.keyframes.txt"
    set zones_file "$prefix/Lily $episode.zones.txt"
    set frame_diff_file "$prefix/Lily $episode.frame diff.txt"
    set strong_noise_file "$prefix/Lily $episode.strong noise.txt"
    SOURCE_FILE=$source_file KEYFRAMES_FILE=$keyframes_file SCENES_FILE=$prezone_scenes_file ZONES_FILE=$zones_file FRAME_DIFF_FILE=$frame_diff_file STRONG_NOISE_FILE=$strong_noise_file python "Lily.prepare.py"
    if not test -e $zones_file
        set_color red ; echo "[prepare] Generated zones file missing. Exiting..." ; set_color normal
        return 126
    end

    set scenes_file "$prefix/Lily $episode.scenes.json"
    if test -e $scenes_file
        rm $scenes_file
    end
    av1an -y --max-tries 10 --temp $temp_dir --verbose --log-level debug -i $source_file --sc-only --scenes $scenes_file --split-method av-scenechange --sc-method standard --extra-split 360 --min-scene-len 6 --encoder svt-av1 --zones $zones_file
    if not test -e $scenes_file
        set_color red ; echo "[prepare] Generated scenes file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Episode number "01"
# $argv[2]: Language "CHS&JPN" (Default) or "CHS"
function encode_h264
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode_h264] Episode number not provided." ; set_color normal
        return 126
    end
    set language $argv[2]
    if test -z $language
        set language "CHS&JPN"
    end

    set prefix ..

    set source_file (find $prefix -regex "$prefix/\[SubsPlease\] Momentary Lily - $episode (1080p) \[[0-9A-F]+\].mkv")
    if not test -e $source_file
        set_color red ; echo "[encode_h264] Source file not found." ; set_color normal
        return 126
    end

    set subtitle_file "$prefix/[SweetSub] Momentary Lily - $episode.chs.ass"
    if not test -e $subtitle_file
        set_color red ; echo "[encode_h264] Subtitle file not found." ; set_color normal
        return 126
    end

    set chapters_file "$prefix/[SweetSub] Momentary Lily - $episode.chapters.txt"
    if not test -e $chapters_file
        set_color red ; echo "[encode_h264] Chapters file not found." ; set_color normal
        return 126
    end
    
    set frame_diff_file "$prefix/Lily $episode.frame diff.txt"
    if not test -e $frame_diff_file
        set_color red ; echo "[encode_h264] Frame diff file not found." ; set_color normal
        return 126
    end

    set strong_noise_file "$prefix/Lily $episode.strong noise.txt"
    if not test -e $strong_noise_file
        set_color red ; echo "[encode_h264] Strong noise file not found." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[encode_h264] Encoding Lily episode $episode..." ; set_color normal
    
    set fonts_dir "$prefix/fonts"
    set video_file "$prefix/Lily $episode.264"
    SOURCE_FILE=$source_file FRAME_DIFF_FILE=$frame_diff_file STRONG_NOISE_FILE=$strong_noise_file SUBTITLE_FILE=$subtitle_file FONTS_DIR=$fonts_dir VSPipe "Lily.h264.py" -c y4m - | x264_x64 --threads 20 --demuxer y4m --output-csp i420 --output-depth 8 --crf 19 --preset veryslow --keyint 360 --min-keyint 1 --ref 13 --deblock 1:1 --rc-lookahead 250 --aq-mode 3 --aq-strength 0.8 --qcomp 0.75 --fade-compensate 0.33 --psy-rd 0.4:0.15 --colorprim bt709 --transfer bt709 --colormatrix bt709 --output $video_file -
    or return $status
    if not test -e $video_file
        set_color red ; echo "[encode_h264] Encoded video file missing. Exiting..." ; set_color normal
        return 126
    end
    
    set audio_file "$prefix/Lily $episode.aac"
    mkvextract $source_file tracks 1:$audio_file
    or return $status
    if not test -e $audio_file
        set_color red ; echo "[encode_h264] Extracted audio file missing. Exiting..." ; set_color normal
        return 126
    end

    set output_file "$prefix/publish/[SweetSub] Momentary Lily - $episode [WebRip][1080P][AVC 8bit][$language].mp4"
    mp4box -add $video_file -add $audio_file -chap $chapters_file -new $output_file
    or return $status
    if not test -e $output_file
        set_color red ; echo "[encode_h264] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end

# $argv[1]: Episode number "01"
function encode_av1
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[encode_av1] Episode number not provided." ; set_color normal
        return 126
    end

    set prefix ..

    set source_file (find $prefix -regex "$prefix/\[SubsPlease\] Momentary Lily - $episode (1080p) \[[0-9A-F]+\].mkv")
    if not test -e $source_file
        set_color red ; echo "[encode_av1] Source file not found." ; set_color normal
        return 126
    end
    
    set scenes_file "$prefix/Lily $episode.scenes.json"
    if not test -e $scenes_file
        set_color red ; echo "[encode_av1] Scenes file not found." ; set_color normal
        return 126
    end
    
    set frame_diff_file "$prefix/Lily $episode.frame diff.txt"
    if not test -e $frame_diff_file
        set_color red ; echo "[encode_av1] Frame diff file not found." ; set_color normal
        return 126
    end

    set strong_noise_file "$prefix/Lily $episode.strong noise.txt"
    if not test -e $strong_noise_file
        set_color red ; echo "[encode_av1] Strong noise file not found." ; set_color normal
        return 126
    end
    
    set_color -o white ; echo "[encode_av1] Encoding Lily episode $episode..." ; set_color normal
    
    set_color -o magenta ; echo "[encode_av1] Encoding server started for episode $episode..." ; set_color normal
    EPISODE=$episode python Lily.server.py &
    
    set video_file "$prefix/Lily $episode.mkv"
    set temp_dir "$prefix/Lily $episode.tmp"
    if test -e $temp_dir
        set_color -o yellow ; echo "[encode_av1] Temp dir already exists. Continuing..." ; set_color normal
    end
    EPISODE=$episode SOURCE_FILE=$source_file FRAME_DIFF_FILE=$frame_diff_file STRONG_NOISE_FILE=$strong_noise_file av1an -y --max-tries 10 --temp $temp_dir --resume --verbose --log-level debug -i "Lily.av1.py" -o $video_file --scenes $scenes_file --chunk-order random --chunk-method bestsource --encoder svt-av1 --pix-format yuv420p10le --workers 5 --video-params "--lp 5 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 --color-range 0" --concat mkvmerge
    or return $status
    if not test -e $video_file
        set_color red ; echo "[encode_av1] Encoded video file missing. Exiting..." ; set_color normal
        return 126
    end

    EPISODE=$episode python Lily.server.shutdown.py
    or return $status
    set_color -o magenta ; echo "[encode_av1] Encoding server stopped for episode $episode..." ; set_color normal
end

# $argv[1]: Episode number "01"
function shutdown_av1
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux_av1] Episode number not provided." ; set_color normal
        return 126
    end

    EPISODE=$episode python Lily.server.shutdown.py
    or return $status
end

# $argv[1]: Episode number "01"
# $argv[2]: Language "CHS&JPN" (Default) or "CHS"
function mux_av1
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[mux_av1] Episode number not provided." ; set_color normal
        return 126
    end
    set language $argv[2]
    if test -z $language
        set language "CHS&JPN"
    end
    
    set prefix ..
    
    set_color -o white ; echo "[mux_av1] Muxing Lily episode $episode..." ; set_color normal

    set source_file (find $prefix -regex "$prefix/\[SubsPlease\] Momentary Lily - $episode (1080p) \[[0-9A-F]+\].mkv")
    if not test -e $source_file
        set_color red ; echo "[mux_av1] Source file not found." ; set_color normal
        return 126
    end

    set video_file "$prefix/Lily $episode.mkv"
    if not test -e $video_file
        set_color red ; echo "[mux_av1] Video file not found." ; set_color normal
        return 126
    end

    set subtitle_file "$prefix/[SweetSub] Momentary Lily - $episode.chs.ass"
    if not test -e $subtitle_file
        set_color red ; echo "[mux_av1] Subtitle file not found." ; set_color normal
        return 126
    end

    set chapters_file "$prefix/[SweetSub] Momentary Lily - $episode.chapters.xml"
    if not test -e $chapters_file
        set_color red ; echo "[mux_av1] Chapters file not found." ; set_color normal
        return 126
    end

    set audio_file "$prefix/Lily $episode.aac"
    mkvextract $source_file tracks 1:$audio_file
    or return $status
    if not test -e $audio_file
        set_color red ; echo "[mux_av1] Extracted audio file missing. Exiting..." ; set_color normal
        return 126
    end

    set fonts_dir "$prefix/fonts"
    set output_fonts_dir "$prefix/Lily $episode.fonts"
    set output_subset_subtitle_file "$output_fonts_dir/[SweetSub] Momentary Lily - $episode.chs.ass"
    if test -e $output_fonts_dir
        rm -r $output_fonts_dir
    end
    ASSFontSubset.Console $subtitle_file --fonts $fonts_dir --output $output_fonts_dir | cat
    or return $status
    if not test -e $output_subset_subtitle_file
        set_color red ; echo "[mux_av1] Output subset subtitle file missing. Exiting..." ; set_color normal
        return 126
    end

    set output_file "$prefix/publish/[SweetSub] Momentary Lily - $episode [WebRip 1080P AV1-10bit AAC $language].mkv"
    set subset_subtitle_file "$prefix/Lily $episode.AssFontSubset.ass"
    mv $output_subset_subtitle_file $subset_subtitle_file
    set font_files
    for f in (find $output_fonts_dir -type f)
        set -a font_files --attach-file
        set -a font_files $f
    end
    mkvmerge --output $output_file --chapters $chapters_file --language 0:jpn $video_file --language 0:jpn $audio_file --language 0:zh-hans $subset_subtitle_file $font_files
    or return $status
    if not test -e $output_file
        set_color red ; echo "[mux_av1] Output file missing. Exiting..." ; set_color normal
        return 126
    end
end
