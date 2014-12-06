#! /usr/bin/env python2

# author: tmv
"""
Act as lirc client to control lights/screen, send IR signals to control equipments
and use wakeonlan to wakeup a media computer.
Requires python-lirc package (sudo apt-get install python-lirc)
For wakeonlan command install wakeonlan from pip (sudo pip install wakeonlan)
lircd daemon must be running
"""

import lirc
import ConfigParser
from wakeonlan import wol
import PiGpioWebClient
import lircirsend
import subprocess
import sys, traceback

_lirc_section = "lirc"

class PiLircControl:
    
    def __init__(self, configFile="HtRoomControl.conf"):
        
        # read the configuration file
        self.config = ConfigParser.ConfigParser()
        self.config.read(configFile)
        
        self.program_name = self.config.get(_lirc_section, "program")
        self.socket = self.config.get(_lirc_section, "socket")
        self.lirc_config = self.config.get(_lirc_section, "config")
        
        # initialize the gpio controller for pi
        self.gpio_controller = PiGpioWebClient.PiGpioWebClient(self.config)
        self.ir_sender = lircirsend.IRSend(self.socket)
        
        # initialize this lirc Client
        self.sock_id = lirc.init(self.program_name, self.lirc_config)
        
    def __del__(self):
        lirc.deinit()
    
    # send an IR signal through lirc    
    def sendIR(self, remote, code):
        directives = [("SEND_ONCE", remote, code)]
        self.ir_sender.send(directives)
    
    # send a command to the pi's gpio web service    
    def doCommand(self, command):
        return self.gpio_controller.doCommand(command)
        
    # start listening to lirc events    
    def run(self):
        
        # initially turn on the lights
        self.gpio_controller.doCommand("lights-on")
        while True:
            codes = lirc.nextcode()
            if codes:
                for code in codes:
                    try:
                        cmd_list = code.split() # dissect the code
                        if cmd_list[0] == "irsend":     # send an IR signal
                            self.sendIR(cmd_list[1], cmd_list[2])
                        elif cmd_list[0] == "wol":      # wake the specified computer (MAC address)
                            wol.send_magic_packet(cmd_list[1])
                        elif cmd_list[0] == "exec":     # execute an external command
                            subprocess.call(cmd_list[1:])
                        elif cmd_list[0] == "python":   # execute a python function
                            python_cmd = cmd_list[1].split(".")
                            the_method = python_cmd[-1]
                            the_module = ".".join(python_cmd[0:-1])
                            getattr(__import__(the_module), the_method)(self)
                        elif cmd_list[0] == "gpio":     # control lights and screen
                            self.doCommand(cmd_list[1])
                    except:
                        e = sys.exc_info()[0]
                        traceback.print_exc()
                        

if __name__ == "__main__":
    import os
    
    # change the working directory to where the script was located
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    lirc_control = PiLircControl()
    lirc_control.run()
