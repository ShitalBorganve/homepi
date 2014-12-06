'''
This is for defining python functions which can be called from the lirc client like
automating the movie watching
'''

import time
from wakeonlan import wol

def start_stop_movie(cmdProcessor):
    ''' cmdProcessor is an instance of CommandProcessor '''
    # get screen status
    screen_status = cmdProcessor.do_gpio_command("screen-read")
    if int(screen_status) == 1:         # screen is down, let's wrap up movie watching 
        # lights up the room
        cmdProcessor.do_gpio_command("light1-on")
        cmdProcessor.do_gpio_command("light2-on")

        # bring up the projector screen
        cmdProcessor.do_gpio_command("screen-off")

        # turn off the projector
        cmdProcessor.send_IR("acer", "KEY_POWER")
        time.sleep(1)
        cmdProcessor.send_IR("acer", "KEY_POWER")
        time.sleep(1)

        # turn off the receiver
        cmdProcessor.send_IR("onkyo", "KEY_POWER")
    else:
        # start movie watching
        xbmc_mac_address = cmdProcessor.config.get("misc", "xbmc_mac_address")

        # setup lights
        cmdProcessor.do_gpio_command("light2-on")
        cmdProcessor.do_gpio_command("light1-off")
        cmdProcessor.do_gpio_command("light3-off")

        # bring down projector screen
        cmdProcessor.do_gpio_command("screen-on")

        # turn on projector
        cmdProcessor.send_IR("acer", "KEY_POWER")
        time.sleep(1)

        # turn on receiver
        cmdProcessor.send_IR("onkyo", "KEY_POWER")    
        time.sleep(2)
        cmdProcessor.send_IR("onkyo", "KEY_DVD")
        
        # wake up media
        wol.send_magic_packet(xbmc_mac_address)
