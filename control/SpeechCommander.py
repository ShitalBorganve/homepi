#!/usr/bin/env python2

# author: tmv
# requires: SpeechRecognition, pyaudio

import ConfigParser as configparser
import speech_recognition as sr
import pyaudio
import logging
import re

class SpeechCommander:
    
    def __init__(self, configFile="SpeechCommander.conf"):
        self.config = configparser.ConfigParser()
        self.config.read(configFile)
        
        # determine the device index to use for mic
        p = pyaudio.PyAudio()
        self.mic_device_name = self.config.get("recognizer", "mic_device")
        self.mic_device = None
        for i in range(p.get_device_count()):
            device_name = p.get_device_info_by_index(i)["name"]
            if device_name == self.mic_device_name:
                self.mic_device = i
                break
                
        p.terminate()

        # process the matches
        self.matches = { }
        for match in self.config.items("matches"):
            self.matches[match[0]] = re.compile(match[1])
        
        self.keywords = self.config.get("recognizer", "keywords").split(",")

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.config.getint("recognizer", "energy_threshold")
        self.recognizer.pause_threshold = self.config.getfloat("recognizer", "pause_threshold")

    def listen(self):
        keyword_mode = True
        while True:
            with sr.Microphone(self.mic_device) as source:
                mode_str = "keyword" if keyword_mode else "command"
                logging.info("Listening for {0} from {1}...".format(mode_str, self.mic_device_name))
                audio = self.recognizer.listen(source)
                logging.info("Phrase captured.")
                
            try:
                phrases = []
                predictions = self.recognizer.recognize(audio, True)
                for prediction in predictions:
                    phrases.append(prediction["text"])
                logging.info("Recognized phrases: " + str(phrases))
                if len(phrases) > 0:
                    if keyword_mode:        # looking for keyword
                        for keyword in self.keywords:
                            if keyword in phrases:
                                logging.info("'{0}' keyword found.".format(keyword))
                                keyword_mode = False
                                break
                    else:
                        # check and execute the command
                        command_ref = None
                        for match_key in self.matches.keys():
                            reg_ex = self.matches[match_key]
                            for phrase in phrases:
                                if reg_ex.search(phrase):   # match is found
                                    command_ref = match_key
                                    break
                            if command_ref:
                                break
                                
                        logging.info("Executing '{0}'".format(command_ref))
                        
                        keyword_mode = True
            
            except LookupError:
                logging.info("No recognize words")
                


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    speechCommander = SpeechCommander()
    speechCommander.listen()
