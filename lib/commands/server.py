import lib.util as util
import lib.server.lib.server_threaded as server
from lib.exceptions import *
from lib.basecommand import Command

class StartServerCommand(Command):
    aliases=["server"]
    def execute(self):
        server.run()
