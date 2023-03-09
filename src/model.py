import cheathelper

class Model:
    command: str = "Choose a command"
    cancel: bool=False
    def get_command(self):
        return cheathelper.get_cheatsheet(self.command)
    def set_command(self, command: str):
        self.command = command
    def get_strcommand(self):
        return self.command
    def get_cancelar(self):
        return self.cancel
    def set_cancelar(self,cancel):
        self.cancel=cancel

