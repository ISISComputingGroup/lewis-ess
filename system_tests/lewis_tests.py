import contextlib
import os
from pathlib import Path
import subprocess
import time

from approvaltests.approvals import verify
from approvaltests.reporters.generic_diff_reporter_factory import \
    GenericDiffReporterFactory
import pytest


TOP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LEWIS_PATH = Path(TOP_DIR) / "scripts/lewis.py"
LEWIS_CONTROL_PATH = Path(TOP_DIR) / "scripts/lewis-control.py"


@contextlib.contextmanager
def julabo_simulation():
    command = ["python", str(LEWIS_PATH), "julabo", "-p",
               "julabo-version-1", "-r", "localhost:10000"]
    proc = subprocess.Popen(command, close_fds=True)
    yield proc
    proc.kill()


def run_control_command(mode, command, value):
    subprocess.check_output(
        ["python", str(LEWIS_CONTROL_PATH), mode, command,
         value]).decode()


def query_device_status():
    return subprocess.check_output(
                ["python", str(LEWIS_CONTROL_PATH), "device"]).decode().replace("\r\n", "\n")


class TestLewis:
    @pytest.fixture(autouse=True)
    def prepare(self):
        self.reporter = GenericDiffReporterFactory().get_first_working()

    def test_list_available_devices(self):
        """
        When: running Lewis without parameters
        Then: returns a list of possible simulations
        """
        result = subprocess.check_output(["python", str(LEWIS_PATH)]).decode()
        verify(result, self.reporter)

    def test_can_query_running_device(self):
        """
        Given: a running Julabo simulation
        When: the control client queries the current state of the simulation
        Then: the current settings are returned
        """
        with julabo_simulation():
            verify(query_device_status(), self.reporter)

    def test_can_change_set_point(self):
        """
        given: a running Julabo simulation
        When: the control client requests a new set-point
        Then: a new set-point is set but the temperature does not change
        """
        with julabo_simulation():
            # Set new setpoint
            run_control_command("device", "set_set_point", "35")
            verify(query_device_status(), self.reporter)

    def test_on_change_set_point_and_circulate_temperature_goes_to_setpoint(
            self):
        """
        Given: a running Julabo simulation
        When: the control client sets a new set-point and tells the device to heat
        Then: the temperature will reach the set-point
        """
        with julabo_simulation():
            # Set the simulation speed to very high, so temperature change is
            # instantaneous
            run_control_command("simulation", "speed", "1000000")

            # Set new setpoint
            run_control_command("device", "set_set_point", "35")

            # Set circulating
            run_control_command("device", "set_circulating", "True")

            time.sleep(0.1)

            verify(query_device_status(), self.reporter)
