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
import sys, traceback
import CommandProcessor

_lirc_section = "lirc"

class PiLircControl:
    
    def __init__(self, configFile="conf/HtRoomControl.conf"):
        
        # read the configuration file
        self.config = ConfigParser.ConfigParser()
        self.config.read(configFile)
        
        self.program_name = self.config.get(_lirc_section, "program")
        self.lirc_config = self.config.get(_lirc_section, "config")
        
        self.command_processor = CommandProcessor.CommandProcessor(self.config)

        # initialize this lirc Client
        self.sock_id = lirc.init(self.program_name, self.lirc_config)
        
    def __del__(self):
        lirc.deinit()
    
    # start listening to lirc events    
    def run(self):
        
        # initially turn on the lights
        self.command_processor.process_command("gpio lights-on")
        while True:
            codes = lirc.nextcode()
            if codes:
                for code in codes:
                    try:
                        self.command_processor.process_command(code)
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
