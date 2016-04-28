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

# Run this in terminal window to monitor device:
#   watch -n 0.1 caget SIM:STATE SIM:LAST_COMMAND SIM:SPEED SIM:SPEED:SP SIM:PHASE SIM:PHASE:SP SIM:PARKPOSITION SIM:PARKPOSITION:SP
run_pcaspy_server(chopper, prefix, pvdb)
