import os
from threading import Thread


class bash_tools:
    def __init__(self):
        pass

    def exec_cmd_command(self, command_word):
        os.system(command_word)

    def network_debug(self, ip, cmd='ping'):
        self.execute_cmd_command('%s %s' % (cmd, ip))

    def exec_iperf(self, args):
        self.execute_cmd_command('iperf3.exe %s' % args)
