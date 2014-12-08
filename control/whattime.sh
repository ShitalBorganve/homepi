#!/bin/bash

# speak the current time using espeak
CURRENT_TIME=$(date +"%I:%M%p")
espeak -ven+f3 "The time is $CURRENT_TIME" >/dev/null 2>&1
