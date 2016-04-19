from mock import call, patch
import unittest

from simulation import CanProcess, CanProcessComposite


class TestCanProcessComposite(unittest.TestCase):
    def test_process_calls_compositeProcess_if_present(self):
        composite = CanProcessComposite()

        with patch.object(composite, 'compositeProcess', create=True) as compositeProcessMock:
            composite.process(3.0)

        compositeProcessMock.assert_called_once_with(3.0)

    def test_iadd_appends_if_is_CanProcess(self):
        composite = CanProcessComposite()

        with patch.object(composite, '_appendSimulation') as appendSimulationMock:
            composite += CanProcess()

        appendSimulationMock.assert_called_once()

    def test_iadd_does_not_append_if_not_CanProcess(self):
        composite = CanProcessComposite()

        with patch.object(composite, '_appendSimulation') as appendSimulationMock:
            composite += None

        appendSimulationMock.assert_not_called()

    @patch.object(CanProcess, 'process')
    def test_init_from_iterable(self, mockProcessMethod):
        simulations = (CanProcess(), CanProcess(),)

        composite = CanProcessComposite(simulations)
        composite.process(4.0)

        mockProcessMethod.assert_has_calls([call(4.0), call(4.0)])
