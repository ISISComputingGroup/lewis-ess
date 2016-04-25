from mock import call, patch
import unittest

from simulation import CanProcess, CanProcessComposite


class TestCanProcess(unittest.TestCase):
    def test_process_calls_doProcess(self):
        processor = CanProcess()

        with patch.object(processor, 'doProcess', create=True) as doProcessMock:
            processor.process(1.0)

        doProcessMock.assert_called_once_with(1.0)

    def test_process_calls_doBeforeProcess_only_if_doProcess_is_present(self):
        processor = CanProcess()

        with patch.object(processor, 'doBeforeProcess', create=True) as doBeforeProcessMock:
            processor.process(1.0)

            doBeforeProcessMock.assert_not_called()

            with patch.object(processor, 'doProcess', create=True):
                processor.process(2.0)

            doBeforeProcessMock.assert_called_once_with(2.0)

    def test_process_calls_doAfterProcess_only_if_doProcess_is_present(self):
        processor = CanProcess()

        with patch.object(processor, 'doAfterProcess', create=True) as doAfterProcess:
            processor.process(1.0)

            doAfterProcess.assert_not_called()

            with patch.object(processor, 'doProcess', create=True):
                processor.process(2.0)

            doAfterProcess.assert_called_once_with(2.0)

    @patch.object(CanProcess, 'process')
    def test_call_invokes_process(self, processMock):
        processor = CanProcess()

        processor(45.0)

        processMock.assert_called_once_with(45.0)


class TestCanProcessComposite(unittest.TestCase):
    def test_process_calls_doBeforeProcess_if_present(self):
        composite = CanProcessComposite()

        with patch.object(composite, 'doBeforeProcess', create=True) as doBeforeProcessMock:
            composite.process(3.0)

        doBeforeProcessMock.assert_called_once_with(3.0)

    def test_addProcessor_if_argument_CanProcess(self):
        composite = CanProcessComposite()

        with patch.object(composite, '_appendProcessor') as appendProcessorMock:
            composite.addProcessor(CanProcess())

        appendProcessorMock.assert_called_once()

    def test_addProcessor_if_argument_not_CanProcess(self):
        composite = CanProcessComposite()

        with patch.object(composite, '_appendProcessor') as appendProcessorMock:
            composite.addProcessor(None)

        appendProcessorMock.assert_not_called()

    def test_init_from_iterable(self):
        with patch.object(CanProcess, 'doProcess', create=True) as mockProcessMethod:
            simulations = (CanProcess(), CanProcess(),)

            composite = CanProcessComposite(simulations)
            composite(4.0)

            mockProcessMethod.assert_has_calls([call(4.0), call(4.0)])
