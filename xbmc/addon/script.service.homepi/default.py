# -*- coding: utf-8 -*-
# author: tmv

import sys, os
import xbmc, xbmcaddon
import urllib2, json

__settings__ = xbmcaddon.Addon(id="script.service.homepi")
__rpi_cmd__ = "http://{host}:{port}/homepi/{pinName}?action={action}"
__lights__ = ["light1", "light2", "light3"]
__screen__ = "screen"

__language__ = __settings__.getLocalizedString

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __settings__.getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (BASE_RESOURCE_PATH)

# construct the command string to be sent to rpi gpio server
def _performCommand(pinName, action="toggle"):
    host = __settings__.getSetting("rpi_host")
    port = __settings__.getSetting("rpi_port")
    cmd_str = __rpi_cmd__.format( \
        host=host, \
        port=port, \
        pinName=pinName, \
        action=action \
    )
    
    response = urllib2.urlopen(cmd_str).read()
    
    result = json.loads(response)
    
    return result[pinName]
    
def _turnOnLights():
    for light in __lights__:
        _performCommand(light, "on")
        
def _turnOffLights():
    for light in __lights__:
        _performCommand(light, "off")
        
def _getScreenStatus():
    return _performCommand(__screen__, "read")
    
class MyXbmcPlayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)
        self.videoPlaying = False
        self.isScreenDown = False
        
    def onPlayBackStarted(self):
        if self.isPlaying() and self.isPlayingVideo():
            self.videoPlaying = True
            # check if the screen is down
            self.isScreenDown = _getScreenStatus()
            if self.isScreenDown:
                # turn off the lights
                _turnOffLights()
                
    def onPlayBackEnded(self):
        if self.videoPlaying:
            self.videoPlaying = False
            if self.isScreenDown:
                # turn light number 2
                _performCommand("light2", "on")
                
    def onPlayBackStopped(self):
        self.onPlayBackEnded()
        
    def onPlayBackPaused(self):
        if self.isPlaying() and self.isPlayingVideo() and self.isScreenDown:
            # turn light number 2
            _performCommand("light2", "on")
            
    def onPlayBackResumed(self):
        if self.isPlaying() and self.isPlayingVideo():
            self.videoPlaying = True
            self.isScreenDown = _getScreenStatus()
            if self.isScreenDown:
                # turn off lights
                _turnOffLights()


xbmc.log("Starting rpi integration service...", xbmc.LOGNOTICE)
player = MyXbmcPlayer()

while not xbmc.abortRequested:
    xbmc.sleep(1000)
