#!/usr/bin/env python

'''
   Python port of irsend.c - a command line utility to send ir commands through LIRC
'''
import socket
import time

LIRCD = "/var/run/lirc/lircd"

class IRSend(object):

    def __init__(self, device=LIRCD, address=None):
        # connect to unix socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # print "Connect to %s" % device
        self.sock.connect(device)
        self.sfile = self.sock.makefile()
        
    def __del__(self):
        self.sock.close()

    def send_packet(self, packet):
        self.packet = packet
        self.sfile.write(packet)
        self.sfile.flush()
        # now read the response
        return self.read_response()

    def read_response(self):
        resp = []
        while True:
            line = self.sfile.readline().strip()
            resp.append(line)
            if line=="END":
                if "SUCCESS" in resp:
                    # print resp
                    return True
                else:
                    # print resp
                    return False
        
    def send(self, codes):
        ''' send the specified codes
            codes: list of tuples of (directive, remote, code) or
                   (directive, remote, code, count)
        '''
        packet = ""
        for code in codes:
            directive = code[0]
            remote = code[1]
            if directive=="SEND_ONCE":
                acode = code[2]
                if len(code)==4:
                    count = code[3]
                else:
                    count = 1
                packet = "%s %s %s %s\n" % (directive, remote, acode, count)
                if not self.send_packet(packet):
                    # print "Error sending packet: %s" % packet
                    pass
            elif directive=="SLEEP":
                # print "Sleep %s" % code[1]
                time.sleep(code[1])    

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser(usage="""%prog -h|--help -v|--version -d|--device -a|--address -c|--count""",
        description=__doc__)
    parser.add_option('-d', '--device', default=LIRCD,
                      help="lircd socket to use")
    parser.add_option('-a', '--address', help="connect to remote lircd at this address")
    parser.add_option('-c', '--count', default=1,
                      help="send command n times")
    (options, args) = parser.parse_args()

    if len(args) < 3:
        parser.error("incorrect number of arguments")
    directive = args[0]
    remote = args[1]
    codes = args[2:]

    # assume directive is "send_once" for now
    code_list = []
    for code in codes:
        code_list.append((directive, remote, code, options.count))

    sender = IRSend(options.device, options.address)
    sender.send(code_list)
