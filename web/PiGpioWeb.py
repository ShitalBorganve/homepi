#! /usr/bin/env python2

# author: tmv
# this implements a simple web service for setting and reading RPi GPIO
# at this time only digital input and output are supported. No analog input yet
# Required packages: python-rpi.gpio, python-webpy

import web, json
import RPi.GPIO as GPIO
import ConfigParser

_GPIO_SECTION = 'gpio'
_WEB_SECTION = 'web'

# use validating specified pin number

_invalid_gpio_pins = [1, 2, 4, 6, 9, 14, 17, 20, 25, 27, 28, 30, 34, 39]

def _isPinValid(pin):
    ''' returns true if the specified pin is valid '''
    maxPin = 40 if GPIO.RPI_REVISION == 3 else 26
    return pin.isdigit() and \
           (int(pin) >= 1) and \
           (int(pin) <= maxPin) and \
           (int(pin) not in _invalid_gpio_pins)

class PiGpioWeb(web.application):
    
    def __init__(self, configFile='rpi_gpio_ws.conf'):
        ''' 
        initialize GPIO based on what's specified in the configuration file
        '''
        
        # load configuration file
        self.config = ConfigParser.ConfigParser()
        self.config.read(configFile)
        
        self.pins = {}              # contains valid pin name

        # setup GPIO
        GPIO.setwarnings(False)         # ignore warnings
        GPIO.setmode(GPIO.BOARD)        # use pin numbering
        
        # setup the pins specified in the configuration
        for key in self.config.options(_GPIO_SECTION):
            value = self.config.get(_GPIO_SECTION, key).split(',')
            if len(value) < 1:
                print('{0} has no specified pin'.format(key))
                continue
                
            pin = value[0]
            if not _isPinValid(pin):
                print('{0} pin for {1} is not valid'.format(pin, key))
                continue
            
            # determine I/O setup
            ioSetup = 'out'             # default setup for the pin
            if len(value) >= 2:
                ioSetup = value[1]
                if ioSetup not in ['in', 'out']:
                    print("io setup for {0} is invalid, using 'out'".format(key))
                    ioSetup = 'out'
                    
            # setup the pin for input or output
            if ioSetup == 'out':
                print('Setting up {0} for output'.format(key))
                GPIO.setup(int(pin), GPIO.OUT)
            else:
                print('Setting up {0} for input'.format(key))
                GPIO.setup(int(pin), GPIO.IN)
            
            # register the key to the list of valid pin names
            self.pins[key] = int(pin)
            
        # set up the web application details
        self.urls = (
            '/homepi', 'GetGpio',       # retrieve states of the io pins specified in configuration
            '/homepi/(.*)', 'GetPin'    # set/get pin using the pin name specified in the config
        )
        
        web.application.__init__(self, self.urls, globals())
        

    def __del__(self):
        # clean up GPIO
        GPIO.cleanup()
        
    def run(self, *middleware):
        """ run the web server """
        func = self.wsgifunc(*middleware)
        host = self.config.get(_WEB_SECTION, 'host')
        port = self.config.getint(_WEB_SECTION, 'port')
        
        return web.httpserver.runsimple(func, (host, port))

class GetGpio:
    """
    Retrieve status of the io specified in the config
    http://<host>:<port>/homepi
    """
    def GET(self):
        # retrieve the application instance
        theApp = web.ctx.app_stack[-1]
        states = { }
        
        # iterate through the pins
        for name, pin in theApp.pins.items():
            pin_state = GPIO.input(pin)     # retrieve the state
            states[name] = pin_state
            
        web.header("Content-Type", "application/json")
        
        return json.dumps(states)
        
class GetPin:
    """
    Set/Get specified pin base on the web context path
    http://<host>:<port>/homepi/<pinAlias> where pinAlias specified in configuration file
    """
    
    def GET(self, pinName):
        # retrieve the application instance
        theApp = web.ctx.app_stack[-1]
        web_params = web.input(action="read")     # toggle is the default action
        
        # check it the specified pinName is properly registered
        if pinName not in theApp.pins.keys():
            raise web.notfound()
            
        result = { }
        pin = theApp.pins[pinName]
        if web_params.action == "on":
            GPIO.output(pin, 1)
        elif web_params.action == "off":
            GPIO.output(pin, 0)
        elif web_params.action == "toggle":
            GPIO.output(pin, not GPIO.input(pin))
            
        result[pinName] = GPIO.input(pin)   # returns the current state of the pin
        
        web.header("Content-Type", "application/json")
        
        return json.dumps(result)
           

if __name__ == '__main__':
    import os
    # change working directory to where the script was run
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    # called from command line
    piGpioWeb = PiGpioWeb()
    piGpioWeb.run()
