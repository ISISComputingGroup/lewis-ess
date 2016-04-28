from adapters import run_pcaspy_server
from simulation import SimulatedChopper

prefix = 'SIM:'
pvdb = {
    'SPEED': {'property': 'speed'},
    'SPEED:SP': {'property': 'targetSpeed'},

    'PHASE': {'property': 'phase'},
    'PHASE:SP': {'property': 'targetPhase'},

    'PARKPOSITION': {'property': 'parkingPosition'},
    'PARKPOSITION:SP': {'property': 'targetParkingPosition'},

    'STATE': {'type': 'string', 'property': 'state'},

    'COMMAND': {'type': 'string',
                'commands': {
                    'START': 'start',
                    'STOP': 'stop',
                    'PHASE': 'phase',
                    'COAST': 'unlock',
                    'PARK': 'park',
                    'INTERLOCK': 'interlock',
                    'RELEASE': 'release'
                },
                'buffer': 'LAST_COMMAND'},

    'LAST_COMMAND': {'type': 'string'}
}

chopper = SimulatedChopper()

run_pcaspy_server(chopper, prefix, pvdb)
