class Bearings(object):
    def __init__(self):
        pass

    def disengage(self):
        pass

    def engage(self):
        pass


class MagneticBearings(Bearings):
    def __init__(self):
        super(MagneticBearings, self).__init__()


class MechanicalBearings(Bearings):
    def __init__(self):
        super(MechanicalBearings, self).__init__()
