from approvaltests.approvals import verify
from approvaltests.reporters.generic_diff_reporter_factory import GenericDiffReporterFactory
import pytest
import subprocess
import os
from pathlib import Path
import time

TOP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LEWIS_PATH = Path(TOP_DIR) / "lewis/lewis.py"
LEWIS_CONTROL_PATH = Path(TOP_DIR) / "lewis/lewis-control.py"

os.environ["PYTHONUNBUFFERED"] = "1"


class TestLewis:
    @pytest.fixture(autouse=True)
    def prepare(self):
        self.reporter = GenericDiffReporterFactory().get_first_working()

    def test_list_available_devices(self):
        result = subprocess.check_output(["python", str(LEWIS_PATH)]).decode()
        verify(result, self.reporter)

    def test_can_query_running_device(self):
        command = ["python", str(LEWIS_PATH), "julabo", "-p", "julabo-version-1", "-r", "localhost:10000"]

        try:
            proc = subprocess.Popen(command, close_fds=True)
            result = subprocess.check_output(["python", str(LEWIS_CONTROL_PATH), "device"]).decode()
            proc.kill()
        except:
            raise Exception("Issue with subprocesses")

        verify(result, self.reporter)

