from simulation import SimulatedChopper


def cycles(c, num):
    for i in range(num):
        c.process(0.1)


if __name__ == '__main__':
    c = SimulatedChopper()

    c.process(0.1)

    c.interlock()

    cycles(c, 4)

    c.targetParkingPosition = 16.0
    c.park()

    cycles(c, 4)

    c.stop()

    cycles(c, 4)

    c.start()

    cycles(c, 1)

    c.unlock()

    cycles(c, 4)

    c.start()

    cycles(c, 4)

    c.lockPhase()

    cycles(c, 4)

    c.stop()

    cycles(c, 1)

    c.start()

    cycles(c, 4)

    c.lockPhase()

    cycles(c, 1)

    c.stop()
