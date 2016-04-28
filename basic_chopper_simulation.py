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

    # 'STATE': {'type': 'string', 'property': 'state'},
}

chopper = SimulatedChopper()

run_pcaspy_server(chopper, prefix, pvdb)
