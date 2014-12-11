'''
This is for defining python functions which can be called from the lirc client or Speech Commander like
automating the movie watching
'''

import time

import subprocess, os
import logging, re
import traceback, sys

def shutil_which(pgm):
    """
    python2 backport of python3's shutil.which()
    """
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p

mpg_player = shutil_which("mpg123")

def say_something(something):
    """Use google tts to translate something to voice played by mpg123"""
    if mpg_player is None:
        logging.error("mpg123 is not installed.")
        return

    import GoogleTTS
    audio_data = GoogleTTS.audio_extract(something)
    process = subprocess.Popen([mpg_player, "--quiet", "-"], stdin=subprocess.PIPE)
    process.communicate(audio_data)

def say_weather(cmdProcessor):
    """ 
        retrieve weather info from yahoo and say the current condition.
        requires pywapi to be installed 
    """
    import pywapi   # must be installed (sudo pip install pywapi)
    location_code = cmdProcessor.config.get("misc", "weather_location_code")
    logging.info("Getting weather from {0}".format(location_code))
    result = pywapi.get_weather_from_yahoo(location_code, "metric")
    strTemplate = "{location}. It's {condition} with temperature of {temperature} celsius. " \
                  "Sunrise at {sunrise} and sunset at {sunset}"
    whatToSay = strTemplate.format(
        location=result['condition']['title'],
        condition=result['condition']['text'],
        temperature=result['condition']['temp'],
        sunrise=result['astronomy']['sunrise'],
        sunset=result['astronomy']['sunset']
    )
    say_something(whatToSay)

def say_command(cmdProcessor, *words):
    words_to_say = " ".join(words)
    say_something(words_to_say)

def start_stop_movie(cmdProcessor):
    ''' cmdProcessor is an instance of CommandProcessor '''
    # wakeonlan must be installed
    from wakeonlan import wol

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

        # turn off the media computer
        xbmc_send = cmdProcessor.config.get("misc", "xbmc_send")
        xbmc_host = cmdProcessor.config.get("misc", "xbmc_host")
        xbmc_port = cmdProcessor.config.get("misc", "xbmc_port")
        if xbmc_send and xbmc_host and xbmc_port:
            subprocess.call(
                [
                    xbmc_send,
                    "--host={0}".format(xbmc_host),
                    "--port={0}".format(xbmc_port),
                    "--action=XBMC.Powerdown"
                ]
            )
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

TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

def say_news(cmdProcessor):
    """
        Retrieve the news from the specified feed in the configuration file
        feedparser package is required (sudo pip install feedparser)
    """
    import feedparser
    
    news_feed_url = cmdProcessor.config.get("misc", "news_feed_url")
    if not news_feed_url:
        logging.error("No newsfeed url specified.")
        return

    logging.info("Retrieving news from {0}".format(news_feed_url))

    # retrieve news
    try:
        feed = feedparser.parse(news_feed_url)
        if len(feed.entries) > 0:
            for entry in feed.entries:
                if entry.has_key("title"):
                    summary = entry["title"].strip()
                    try:
                        say_something(summary)
                    except:
                        pass    # ignore error
                time.sleep(1)
            say_something("Done with the news")
        else: 
            say_something("No news to report")
    except:
        e = sys.exc_info()[0]
        traceback.print_exc()
        say_something("There was a problem retrieving the news. Please check log.")
