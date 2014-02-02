class Command(object):
    def __init__(self, *args, **kwargs):
        self.params = kwargs.get('params', {})
        self.args = kwargs.get('args', None)

    def execute(self):
        raise NotImplementedError()