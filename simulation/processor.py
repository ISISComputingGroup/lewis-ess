class CanProcess(object):
    """
    The CanProcess class is meant as a base for all things that
    are able to process on the bases of a time delta (dt).

    The base implementation does nothing.

    There are three methods that can be implemented by sub-classes and are called in the process-method in this order:

        1. doBeforeProcess
        2. doProcess
        3. doAfterProcess

    The doBefore- and doAfterProcess methods are only called if a doProcess-method exists.
    """

    def __init__(self):
        super(CanProcess, self).__init__()

    def __call__(self, dt):
        self.process(dt)

    def process(self, dt):
        if hasattr(self, 'doProcess'):
            if hasattr(self, 'doBeforeProcess'):
                self.doBeforeProcess(dt)

            self.doProcess(dt)

            if hasattr(self, 'doAfterProcess'):
                self.doAfterProcess(dt)


class CanProcessComposite(CanProcess):
    """
    This subclass of CanProcess is a convenient way of collecting
    multiple items that implement the CanProcess interface.

    Items can be added to the composite like this:

        composite = CanProcessComposite()
        composite.addProcessor(item_that_implements_CanProcess)

    The process-method calls the process-method of each contained
    item. Specific things that have to be done before or after the
    containing items are processed can be implemented in the doBefore-
    and doAfterProcess methods.
    """

    def __init__(self, iterable=()):
        super(CanProcessComposite, self).__init__()

        self._processors = []

        for item in iterable:
            self.addProcessor(item)

    def addProcessor(self, other):
        if isinstance(other, CanProcess):
            self._appendProcessor(other)

    def _appendProcessor(self, processor):
        self._processors.append(processor)

    def doProcess(self, dt):
        for processor in self._processors:
            processor.process(dt)
