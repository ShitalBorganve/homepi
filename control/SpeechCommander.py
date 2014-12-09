#!/usr/bin/env python2

# author: tmv
# for voice control
# requires: SpeechRecognition, pyaudio

import ConfigParser as configparser
import speech_recognition as sr
import pyaudio, wave
import logging
import re, subprocess
import CommandProcessor
import sys, traceback, time
import GoogleTTS
import thread

from collections import deque

def shutil_which(pgm):
    """
    python2 backport of python3's shutil.which()
    """
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p

class SpeechCommander:
    
    def __init__(self, configFile="conf/HtRoomControl.conf"):
        self.config = configparser.ConfigParser()
        self.config.read(configFile)
        
        # determine the device index to use for mic
        self.pyaudio = pyaudio.PyAudio()
        self.mic_device_name = self.config.get("recognizer", "mic_device")
        self.out_device_name = self.config.get("recognizer", "out_device")
        self.mic_device = self._get_device_index(self.mic_device_name)
        self.out_device = self._get_device_index(self.out_device_name)

        # process the matches
        self.matches = { }
        wildcard_str = "[\w\s]*"
        for match in self.config.items("matches"):
            # convert the matches to regular expressions
            re_list = match[1].split("|")
            self.matches[match[0]] = []
            for re_str in re_list:
                reg_ex = wildcard_str + wildcard_str.join(re_str.split()) + wildcard_str
                self.matches[match[0]].append(re.compile(reg_ex, re.IGNORECASE))
        
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

    def _get_device_index(self, name):
        ''' returns the index for the specified name '''
        p = self.pyaudio
        result = -1
        for idx in range(p.get_device_count()):
            if p.get_device_info_by_index(idx) == name:
                result = idx
                break
                
        return result

    def playMp3(self, something):
        mp3_player = self.config.get("recognizer", "mp3_player").split()
        process = subprocess.Popen(mp3_player, stdin=subprocess.PIPE)
        process.communicate(something)

    def saySomething(self, something):
        self.playMp3(GoogleTTS.audio_extract(something))
        
        
    def playSound(self, waveFile):
        chunk = 1024
        p = self.pyaudio
        wf = wave.open(waveFile, "rb")
        
        stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                        channels = wf.getnchannels(),
                        rate = wf.getframerate(),
                        output_device_index = self.out_device,
                        output = True)
        
        data = wf.readframes(chunk)
        
        while data != '':
            stream.write(data)
            data = wf.readframes(chunk)
            
        wf.close()
        stream.close()

    def captureVoice(self):
        """ this is the thread which captures voice input from microphone """
        
        while True:
            logging.info("Waiting for voice command...")

            with sr.Microphone(self.mic_device) as source:
                audio = self.recognizer.listen(source)
            
            logging.info("A voice is detected.")

            # put the captured audio into the queue
            with self.thread_lock:
                self.voiceQueue.append(audio)
                
    def processVoice(self):
        """ process the captured voices """
        keyword_mode = True and not self.force_command
        while True:
            try:
                with self.thread_lock:
                    audio = self.voiceQueue.popleft()
            except IndexError:
                # no data to process in the queue
                continue
            
            logging.info("Processing in {0} mode...".format("keyword" if keyword_mode else "command"))
    
            # process the retrieved audio
            phrases = []
            try:
                predictions = self.recognizer.recognize(audio, True)
                for prediction in predictions:
                    phrases.append(prediction["text"])
                logging.info("Recognized phrases: {0}".format(str(phrases)))

                # special handling for thank you
                if "thank you" in phrases:
                    self.saySomething("You're welcome")
                    keyword_mode = True and not self.force_command
                    continue

                if len(phrases) > 0:
                    if keyword_mode:        # looking for keyword
                        for keyword in self.keywords:
                            if keyword in phrases:
                                logging.info("'{0}' keyword found.".format(keyword))
                                keyword_mode = False
                                self.playMp3(self.keyword_ack_response)
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
                            self.playMp3(self.command_ack_response)
                            self.cmdProcessor.process_command(command)                    
                        keyword_mode = True and not self.force_command
        
            except LookupError:
                logging.info("No recognize words")
                if not keyword_mode:
                    self.playMp3(self.lookup_error_response)

            except:
                e = sys.exc_info()[0]
                traceback.print_exc()
                keyword_mode = True and not self.force_command
                    

    def listen(self):
        # retrieve from google possible responses
        self.ready_response = GoogleTTS.audio_extract(self.config.get("recognizer", "ready_response"))
        self.keyword_ack_response = GoogleTTS.audio_extract(self.config.get("recognizer", "keyword_ack"))
        self.command_ack_response = GoogleTTS.audio_extract(self.config.get("recognizer", "command_ack"))
        self.lookup_error_response = GoogleTTS.audio_extract(self.config.get("recognizer", "lookup_error_response"))
        self.playMp3(self.ready_response)
        self.voiceQueue = deque()     # initialize to an empy queue
        self.thread_lock = thread.allocate_lock()
        
        # starts the 2 threads
        thread.start_new_thread(self.captureVoice, ())
        thread.start_new_thread(self.processVoice, ())

        # wait forever
        while True:
            time.sleep(1)
        
if __name__ == "__main__":
    import os

    # change the working directory to where the script was located
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)    
    
    logging.basicConfig(level=logging.INFO)

    speechCommander = SpeechCommander()
    speechCommander.listen()
