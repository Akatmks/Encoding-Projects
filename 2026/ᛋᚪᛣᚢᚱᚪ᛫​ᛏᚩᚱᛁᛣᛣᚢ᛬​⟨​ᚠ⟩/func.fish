#!/usr/bin/env fish

# $argv[1]: Episode number "01"
function audio
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[filter] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[filter] Making audio for $episode..." ; set_color normal

    set source_file (python information.py source $episode)
    or return $status
    set trim_start (python information.py trim_start $episode)
    or return $status
    set main_audio_file "Main/$episode.flac"
    set main_audio_file_win "Main\\$episode.flac"
    if test $trim_start = None
        eac3to (python information.py source $episode) 2: $main_audio_file_win -normal -log=/dev/null
        or return $status
    else
        eac3to (python information.py source $episode) 2: $main_audio_file_win -(math $trim_start / 24 "*" 1001)ms -normal -log=/dev/null
        or return $status
    end

    set mini_audio_file "Mini/$episode.opus"
    opusenc $main_audio_file $mini_audio_file --bitrate 128
end


# $argv[1]: Episode number "01"
function intermediate
    set episode $argv[1]
    if test -z $episode
        set_color red ; echo "[filter] Episode number not provided." ; set_color normal
        return 126
    end

    set_color -o white ; echo "[filter] Filtering $episode..." ; set_color normal

    set intermediate_file "$INTERMEDIATE_DIR/$episode.mkv"
    if test -e $intermediate_file
        set_color red ; echo "[filter] Intermediate file already exists. Exiting..." ; set_color normal
        return 126
    end
    EPISODE=$episode python intermediate.py
    or return $status
    if not test -e $intermediate_file
        set_color red ; echo "[filter] Intermediate file missing. Exiting..." ; set_color normal
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
        return 126
    else
        EPISODE=$episode python main.py &
    end

    set mini_encode "Mini/$episode.ivf"
    if test -e $mini_encode
        set_color red ; echo "[encode] Mini encode file already exists. Skipping mini encode..." ; set_color normal
        return 126
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

    rm -rf "__pycache__" "Temp/$episode.vsmuxtools.tmp"

    if test -n "$clean_ia"
        rm -f "$INTERMEDIATE_DIR/$episode.mkv" "Main/$episode.flac" "Mini/$episode.opus"
    end
end
