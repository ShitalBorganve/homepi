#!/bin/sh

# this tells the current time
GOOGLE_TTS="GoogleTTS.py"
MP3_PLAYER="/usr/bin/mpg123 --quiet"
CURRENT_TIME=$(date +"%I:%M%p")
PYTHON=/usr/bin/python2

$PYTHON $GOOGLE_TTS -s "Current time is $CURRENT_TIME" | $MP3_PLAYER -
