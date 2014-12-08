#!/bin/bash

# speak the current time using espeak
CURRENT_DATE=$(date +"%A, %B %d, %Y")
espeak -ven+f3 "Today is $CURRENT_DATE" >/dev/null 2>&1
