#!/bin/sh

# this tells the current time
GOOGLE_TTS="GoogleTTS.py"
MP3_PLAYER="/usr/bin/mpg123 --quiet"
CURRENT_DATE=$(date +"%A, %B %d, %Y")
PYTHON=/usr/bin/python2

$PYTHON $GOOGLE_TTS -s "Today is $CURRENT_DATE" | $MP3_PLAYER -
