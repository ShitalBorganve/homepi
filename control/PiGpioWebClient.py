#! /usr/bin/env python2

# author: tmv
# communicates to the pi GPIO web service to control the lights and screen in my HT room

import urllib2, json
import ConfigParser

# this is the template for issuing commands to the web service
_BASE_CMD_STR="http://{host}:{port}/homepi/{pinAlias}?action={action}"
_WS_SECTION="homepi-web"

class PiGpioWebClient:

    def __init__(self, config):
        
        # read the configuration file
        self.config = config                # config must be an instance of ConfigParser read already
        
        self.host = self.config.get(_WS_SECTION, "host")
        self.port = self.config.getint(_WS_SECTION, "port")
        
        # get the available lights
        self.lights = self.config.get(_WS_SECTION, "lights").split(",")

        self.valid_pins = self.config.get(_WS_SECTION, "valid_pins").split(",")        
        self.valid_cmds = self.config.get(_WS_SECTION, "valid_cmds").split(",")
        
    def _performAction(self, pinName, action="toggle"):
        full_url = _BASE_CMD_STR.format( \
            host=self.host, \
            port=self.port, \
            pinAlias=pinName, \
            action=action \
        )
        response = urllib2.urlopen(full_url).read()
        result = json.loads(response)   # convert json string to object
        
        return result[pinName]
        
    def _performActions(self, pins, action="toggle"):
        result = ""
        for pin in pins:
            result = result + str(self._performAction(pin, action))
            
        return int(result)
        
    def doCommand(self, command):
        """ parse the specified command and perform the action """
        cmds = command.split("-")
        if cmds[1] not in self.valid_cmds:
            return -1       # ignore if invalid command
        if cmds[0] not in self.valid_pins:
            return -1       # ignore if invalid pin
            
        if cmds[0] == "lights":     # special word for controlling all the lights
            return self._performActions(self.lights, cmds[1])
            
        return self._performAction(cmds[0], cmds[1])

if __name__ == "__main__":
    import sys
    numArgs = len(sys.argv)
    if ( numArgs >= 2 ):
        config = ConfigParser.ConfigParser()
        config.read("conf/HtRoomControl.conf")
        controller = PiGpioWebClient(config)
        for argNo in range(1, numArgs):
            cmd = sys.argv[argNo]
            print controller.doCommand(cmd)
