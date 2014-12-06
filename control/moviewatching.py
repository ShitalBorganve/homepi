'''
This is for defining python functions which can be called from the lirc client like
automating the movie watching
'''

import time
from wakeonlan import wol

def start_stop_movie(lirc_client):
    ''' lirc_client is an instance of PiLircControl '''
    # get screen status
    screen_status = lirc_client.doCommand("screen-read")
    if int(screen_status) == 1:         # screen is down, let's wrap up movie watching 
        # lights up the room
        lirc_client.doCommand("light1-on")
        lirc_client.doCommand("light2-on")

        # bring up the projector screen
        lirc_client.doCommand("screen-off")

        # turn off the projector
        lirc_client.sendIR("acer", "KEY_POWER")
        time.sleep(1)
        lirc_client.sendIR("acer", "KEY_POWER")
        time.sleep(1)

        # turn off the receiver
        lirc_client.sendIR("onkyo", "KEY_POWER")
    else:
        # start movie watching
        xbmc_mac_address = lirc_client.config.get("misc", "xbmc_mac_address")

        # setup lights
        lirc_client.doCommand("light2-on")
        lirc_client.doCommand("light1-off")
        lirc_client.doCommand("light3-off")

        # bring down projector screen
        lirc_client.doCommand("screen-on")

        # turn on projector
        lirc_client.sendIR("acer", "KEY_POWER")
        time.sleep(1)

        # turn on receiver
        lirc_client.sendIR("onkyo", "KEY_POWER")    
        time.sleep(2)
        lirc_client.sendIR("onkyo", "KEY_DVD")
        
        # wake up media
        wol.send_magic_packet(xbmc_mac_address)
