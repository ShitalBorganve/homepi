# author tmv
# for processing commands

from wakeonlan import wol
import PiGpioWebClient
import lircirsend
import subprocess
import ConfigParser
import cmdutils

class CommandProcessor:
    def __init__(self, config):
        self.config = config
        
        # these objects will be used in actual processing of commands
        self.gpio_controller = PiGpioWebClient.PiGpioWebClient(self.config)
        self.ir_sender = lircirsend.IRSend(self.config.get("lirc", "socket"))
        
    def send_IR(self, remote, code):
        directives = [("SEND_ONCE", remote, code)]
        self.ir_sender.send(directives)
        
    def do_gpio_command(self, command):
        return self.gpio_controller.doCommand(command)
        
    def process_command(self, command):
        cmd_list = command.split()
        if cmd_list[0] == "irsend":     # send IR signal
            self.send_IR(cmd_list[1], cmd_list[2])
        elif cmd_list[0] == "wol":      # wake on lan command
            wol.send_magic_packet(cmd_list[1])
        elif cmd_list[0] == "exec":     # execute an external command
            subprocess.call(cmd_list[1:])
        elif cmd_list[0] == "python":   # execute a python script
            python_cmd = cmd_list[1].split(".")
            the_method = python_cmd[-1]
            the_params = None
            if len(cmd_list) > 2:
                the_params = cmd_list[2:]   # retrieve the list of parameters

            the_module = ".".join(python_cmd[0:-1])
            method_attr = getattr(__import__(the_module), the_method)
            if the_params is None:
                method_attr(self)
            else:
                method_attr(self, *the_params)
        elif cmd_list[0] == "gpio":     # control rpi gpio
            self.do_gpio_command(cmd_list[1])
        elif cmd_list[0] == "say":
            cmdutils.say_something(" ".join(cmd_list[1:]))

if __name__ == "__main__":
    import os

    # change the working directory to where the script was located
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    import sys
    configFile = "HtRoomControl.conf"
    
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    cmdProcessor = CommandProcessor(config)
    if len(sys.argv) > 2:
        command = " ".join(sys.argv[1:])
        cmdProcessor.process_command(command)
    
