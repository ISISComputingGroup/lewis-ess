class Test(object):
    def foo(self):
        return 1;


class Stuff(object):
    def __init__(self):
        self._a = 0
        self._b = (0, 0)

        self.g = 'test'

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        if value < 0:
            raise ValueError('No values < 0!')

        self._a = value

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, one):
        self._b = one

    @property
    def c(self):
        return self._a + self._b[0]

    def doIt(self):
        self._a = 42

    def doItNow(self, foo, bar=34):
        self._a = foo
        self._b = (self._b[0], bar)

    def getTest(self):
        return Test()


from core.rpc_server import RPCObjectCollection, ZMQJSONRPCServer
from time import sleep


s = Stuff()
c = RPCObjectCollection.create([(s, 's'), (Stuff(), 'b')])

server = ZMQJSONRPCServer(c)

while True:
    server.process()
    sleep(0.1)
