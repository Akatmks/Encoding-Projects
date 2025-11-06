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
    EPISODE=$episode python intermediate.py
    or return $status
    if not test -e $intermediate_file
        set_color red ; echo "[encode] Intermediate file missing. Exiting..." ; set_color normal
        return 126
    end
end
