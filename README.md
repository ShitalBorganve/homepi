homepi
======

These contain set of files for automating home theater room using Raspberry Pi's GPIO. 
You can connect relay switches to Pi's GPIO pins, and use this set of programs to 
control your room lighting and projector screen. The following components are included:
<ul>
  <li>
    <samp>web/PiGpioWeb.py</samp> - implements a web application which accesses and controls GPIO switches. 
    You can control through <samp>http://<i>host</i>:<i>port</i>/homepi/<i>pinAlias</i>?action=<i>action</i></samp> 
    where <samp><i>pinAlias</i></samp> is an alias for GPIO pin defined in the configuration file 
    (<samp>rpi_gpio_ws.conf</samp>), and <samp><i>action</i></samp> is either <samp>on</samp>, <samp>off</samp>, 
    or <samp>read</samp>. Please check out <samp>rpi_gpio_ws.conf</samp> on configuring the web application. 
    You need to install python-rpi.gpio and python-webpy modules.
    <pre>sudo apt-get install python-rpi.gpio python-webpy</pre>
  </li>
  <li>
    <samp>web/PiLircControl.py</samp> - implements a lircd event listener similar to irexec. With this program, you
    can use remote controls or input devices supported by lirc to do the following:
    <ul>
      <li>control lights, and projector screen</li>
      <li>send IR signals to control electronic devices such as tv/projector and a/v receiver</li>
      <li>wake a media computer through wakeonlan facility</li>
      <li>execute an external program or script</li>
      <li>invoke a python function</li>
    </ul>
    The directives can be defined in <samp>lirccontrol.conf</samp>. This follows the same format as the
    configuration file for irexec included in the lirc package. The program reads its configuration from 
    <samp>HtRoomControl.conf</samp>. The lircd daemon must be running before invoking this program. In addition, python-lirc
    package must be installed. For wakeonlan facility, install <samp>wakeonlan</samp> through pip.
    <pre>
      sudo apt-get install lirc, python-lirc
      sudo pip install wakeonlan
    </pre>
  </li>
  <li>
    <samp>xbmc/addon/script.service.homepi</samp> - xbmc (now kodi) addon to automatically control lights when projector
    screen is down. Copy this directory to $HOME/.xbmc/addons on your xbmc media computer. Restart xbmc and configure the
    addon by providing the host/ip and port where the <samp>PiGpioWeb.py</samp> is deployed. This addon automatically turns off
    the lights when a video playback has started/resumed, and turns the lights on when playback is paused/stopped/finished.
  </li>
  <li>
    <i>in progress: control through voice recognition<i>
  </li>
</ul>
