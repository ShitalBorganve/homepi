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
</ul>
