#!/usr/bin/env python2

# author: tmv
# for voice control
# requires: SpeechRecognition, pyaudio

import ConfigParser as configparser
import speech_recognition as sr
import pyaudio, wave
import logging
import re
import CommandProcessor
import sys, traceback

class SpeechCommander:
    
    def __init__(self, configFile="HtRoomControl.conf"):
        self.config = configparser.ConfigParser()
        self.config.read(configFile)
        
        # determine the device index to use for mic
        self.pyaudio = pyaudio.PyAudio()
        p = self.pyaudio
        self.mic_device_name = self.config.get("recognizer", "mic_device")
        self.mic_device = None
        for i in range(p.get_device_count()):
            device_name = p.get_device_info_by_index(i)["name"]
            if device_name == self.mic_device_name:
                self.mic_device = i
                break

        # process the matches
        self.matches = { }
        wildcard_str = "[\w\s]*"
        for match in self.config.items("matches"):
            # convert the matches to regular expressions
            re_list = match[1].split("|")
            self.matches[match[0]] = []
            for re_str in re_list:
                reg_ex = wildcard_str + wildcard_str.join(re_str.split()) + wildcard_str
                self.matches[match[0]].append(re.compile(reg_ex))
        
        self.keywords = self.config.get("recognizer", "keywords").split("|")

        # initialize command processor
        self.cmdProcessor = CommandProcessor.CommandProcessor(self.config)
        self.commands = dict(self.config.items("commands"))

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.config.getint("recognizer", "energy_threshold")
        self.recognizer.pause_threshold = self.config.getfloat("recognizer", "pause_threshold")
        self.command_duration = self.config.getint("recognizer", "command_duration")
        self.force_command = self.config.getboolean("recognizer", "force_command")

    def __del__(self):
        self.pyaudio.terminate()

    def playSound(self, waveFile):
        chunk = 1024
        p = self.pyaudio
        wf = wave.open(waveFile, "rb")
        
        stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                        channels = wf.getnchannels(),
                        rate = wf.getframerate(),
                        output = True)
        
        data = wf.readframes(chunk)
        
        while data != '':
            stream.write(data)
            data = wf.readframes(chunk)
            
        wf.close()
        stream.close()

    def listen(self):
        keyword_mode = True
        with sr.Microphone(self.mic_device) as source:
            while True:
                mode_str = "keyword" if keyword_mode and not self.force_command else "command"
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
                        if keyword_mode and not self.force_command:        # looking for keyword
                            for keyword in self.keywords:
                                if keyword in phrases:
                                    logging.info("'{0}' keyword found.".format(keyword))
                                    keyword_mode = False
                                    self.playSound("yes.wav")
                                    break
                        else:
                            # check and execute the command
                            command_ref = None
                            for phrase in phrases:
                                for match_key in self.matches.keys():
                                    for reg_ex in self.matches[match_key]:
                                        if reg_ex.search(phrase):   # match is found
                                            command_ref = match_key
                                            break
                                    if command_ref:
                                        break
                                if command_ref:
                                    break
                                
                            logging.info("Executing '{0}'".format(command_ref))
                            command = self.commands[command_ref]
                            if command:
                                self.playSound("affirmative.wav")
                                self.cmdProcessor.process_command(command)
                        
                            keyword_mode = True
            
                except LookupError:
                    logging.info("No recognize words")

                except:
                    e = sys.exc_info()[0]
                    traceback.print_exc()
                    keyword_mode = True

if __name__ == "__main__":
    import os

    # change the working directory to where the script was located
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)    
    
    logging.basicConfig(level=logging.INFO)

    speechCommander = SpeechCommander()
    speechCommander.listen()
