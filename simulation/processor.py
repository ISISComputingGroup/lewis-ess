class CanProcess(object):
    def __init__(self):
        super(CanProcess, self).__init__()

    def process(self, dt):
        pass


class CanProcessComposite(CanProcess):
    def __init__(self, iterable=()):
        super(CanProcessComposite, self).__init__()

        self._processors = []

        for item in iterable:
            self.__iadd__(item)

    def __iadd__(self, other):
        if isinstance(other, CanProcess):
            self._appendSimulation(other)

    def _appendSimulation(self, other):
        self._processors.append(other)

    def process(self, dt):
        if hasattr(self, 'compositeProcess'):
            self.compositeProcess(dt)

        for simulation in self._processors:
            simulation.process(dt)
