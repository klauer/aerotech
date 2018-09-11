'''
A simple pydm data plugin for direct communication with Aerotech Ensemble
controllers

Usage:
    $ export PYDM_DATA_PLUGINS_PATH=$PWD/pydm_plugin
    $ echo "Ensure this directory exists: $PYDM_DATA_PLUGINS_PATH"
    $ pydm
'''
import asyncio
import logging
import threading
import enum
import ast

import aerotech
import numpy as np

from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from pydm.PyQt.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer
from pydm.PyQt.QtGui import QApplication
from pydm.utilities import is_pydm_app


logger = logging.getLogger(__name__)


class Severity(enum.IntEnum):
    NO_ALARM = 0
    MINOR = 1
    MAJOR = 2
    INVALID = 3


class ClientThread(QThread):
    _comm_cache = {}

    def __init__(self, host, port, loop=None):
        super().__init__()
        if loop is None:
            loop = asyncio.new_event_loop()

        self.host = host
        self.port = port
        self.loop = loop
        self.lock = threading.Lock()
        self.comm = None

    def run(self):
        logger.info("New EnsembleComm client %s:%d", self.host, self.port)
        loop = self.loop
        iglobal = None
        asyncio.set_event_loop(loop)
        while not self.isInterruptionRequested():
            with self.lock:
                if self.comm is None and not self.isInterruptionRequested():
                    comm = aerotech.EnsembleComm(self.host, self.port,
                                                 loop=loop)
                    iglobal = comm.iglobal(0)
                    try:
                        loop.run_until_complete(iglobal.get())
                    except (ConnectionResetError, ConnectionRefusedError,
                            aerotech.AeroException) as ex:
                        logger.exception('Connection failed...')
                        self.sleep(1)
                        continue

                    logger.info("Connected to %s:%d", self.host, self.port)
                    self.comm = comm
                else:
                    try:
                        coro = self.comm.write_read('INVALID_CMD')
                        loop.run_until_complete(coro)
                    except aerotech.FailureResponseException as ex:
                        logger.debug('Crosstalk check OK')
                    except Exception as ex:
                        self.comm = None
                        logger.exception('Connection failed...')
                    else:
                        self.comm = None
                        logger.error('Communication mismatch / crosstalk '
                                     'with another process. Disconnecting.')
                        self.sleep(5)

            self.sleep(1)

    def disconnect(self):
        with self.lock:
            if self.comm is not None:
                self.loop.call_soon_threadsafe(self.comm.close())
                self.comm = None


def get_client(host, port, loop=None):
    ident = (host, port, loop)
    try:
        return ClientThread._comm_cache[ident]
    except KeyError:
        inst = ClientThread(host, port, loop=loop)
        ClientThread._comm_cache[ident] = inst
        inst.start()
        return inst


class PollThread(QThread):
    new_data_signal = pyqtSignal(object)
    new_severity_signal = pyqtSignal(int)
    writable = False

    def __init__(self, connection, client, parameter, *, poll_rate=0.1):
        super().__init__()
        self.connection = connection
        self.poll_rate_ms = int(poll_rate * 1000)
        self.client = client
        self.parameter = parameter
        self.start()

    def run(self):
        loop = self.client.loop
        failed_rate = self.poll_rate_ms * 2
        while not self.isInterruptionRequested():
            if self.client.comm is None:
                self.new_severity_signal.emit(Severity.INVALID)
                self.msleep(failed_rate)
                continue

            with self.client.lock:
                sleep_ms = failed_rate
                comm = self.client.comm
                if comm is None:
                    self.new_severity_signal.emit(Severity.INVALID)
                else:
                    try:
                        data = self.query(comm, loop)
                        if asyncio.iscoroutine(data):
                            data = loop.run_until_complete(data)
                    except (BrokenPipeError, ConnectionResetError) as ex:
                        logger.error('Poll failed; connection lost')
                        self.client.comm = None
                        sleep_ms = failed_rate * 2
                        self.new_severity_signal.emit(Severity.INVALID)
                    except aerotech.FailureResponseException as ex:
                        logger.warning('Query failed: %s', self.parameter)
                        self.new_severity_signal.emit(Severity.MAJOR)
                    except aerotech.FaultResponseException as ex:
                        logger.warning('Query fault: %s', self.parameter)
                        self.new_severity_signal.emit(Severity.MAJOR)
                    except aerotech.TimeoutResponseException as ex:
                        logger.warning('Query timed out: %s', self.parameter)
                        self.new_severity_signal.emit(Severity.MINOR)
                    except Exception as ex:
                        logger.exception('Poll failed')
                        self.new_severity_signal.emit(Severity.MAJOR)
                    else:
                        sleep_ms = self.poll_rate_ms
                        self.new_severity_signal.emit(Severity.NO_ALARM)
                        data = self.fix_value(data)
                        logger.debug('%s => %s', self.parameter, data)
                        self.new_data_signal.emit(data)
            self.msleep(sleep_ms)

    def fix_value(self, value):
        try:
            return ast.literal_eval(value)
        except Exception:
            return value

    def query(self, comm, loop):
        # Return a coroutine that gets waited on above
        return comm.write_read(self.parameter)


class PollThreadTaskState(PollThread):
    enum_strings = ('unknown', 'idle', 'ready', 'running', 'paused', 'done',
                    'errored',
                    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection.enum_strings_signal.emit(self.enum_strings)

    def query(self, comm, loop):
        self.connection.enum_strings_signal.emit(self.enum_strings)
        return super().query(comm, loop)


class PollThreadAxisStatus(PollThread):
    def fix_value(self, value):
        try:
            value = int(value)
        except Exception as ex:
            return value

        if value < 0:
            value = 2 ** 32 + value

        # NOTE: emitting a 32-bit unsigned value from a signal with certain (?)
        # versions of sip/pyqt can cause it to be re-interpreted on the slot
        # side as a 32-bit signed integer, unexpectedly. use ndarray here to
        # work around that:
        value = np.array(value, dtype=np.uint32)
        return value


class WriteOnlyParameter(QThread):
    new_data_signal = pyqtSignal(object)
    new_severity_signal = pyqtSignal(int)
    writable = True

    def __init__(self, connection, client, parameter, *, poll_rate=None):
        super().__init__()
        self.connection = connection
        self.client = client
        self.parameter = parameter
        self.to_write = []

    def run(self):
        try:
            loop = self.client.loop
            while self.to_write:
                comm = self.client.comm
                if comm is None:
                    logger.warning('Not writing %s; disconnected',
                                   self.parameter)
                    self.to_write.clear()
                    break

                with self.client.lock:
                    value = self.to_write.pop(0)
                    cmd = self.parameter.format(value=value)
                    coro = comm.write_read(cmd)
                    try:
                        result = loop.run_until_complete(coro)
                    except Exception as ex:
                        logger.exception('Write failed: %r', cmd)
                        self.new_severity_signal.emit(Severity.MAJOR)
                        self.to_write.clear()
                        break
                    else:
                        logger.info('Write result: %r => %s', cmd, result)
                        self.new_severity_signal.emit(Severity.NO_ALARM)
        except Exception:
            logger.exception('Write failed!')

    def write(self, value):
        logger.debug('%s write: %s', self.parameter, value)
        self.to_write.append(value)
        self.start()


def is_write_only(parameter):
    prefixes = ['ENABLE',
                'DISABLE',
                'MOVEINC',
                'MOVEABS',
                'LINEAR',
                ]

    if any(parameter.startswith(item) for item in prefixes):
        return True

    return (parameter in ('RESET', 'COMMITPARAMETERS'))


def parse_address(addr):
    'ensemble://<host>[:<port>][/@poll_rate]/<parameter>'
    host_info, _, parameter = addr.partition('/')

    if ':' in host_info:
        host, port = host_info.split(':')
    else:
        host, port = host_info, 8000

    if parameter.startswith('@') and '/' in parameter:
        poll_info, _, parameter = parameter.partition('/')
        poll_rate = poll_info.lstrip('@')
    else:
        poll_rate = 0.5

    if parameter.startswith('TASKSTATE'):
        cls = PollThreadTaskState
    elif (parameter.startswith('AXISSTATUS') or
          parameter.startswith('AXISFAULT')):
        cls = PollThreadAxisStatus
    elif is_write_only(parameter):
        cls = WriteOnlyParameter
    else:
        cls = PollThread

    return {'host': host,
            'port': int(port),
            'poll_rate': float(poll_rate),
            'parameter': parameter,
            'data_class': cls,
            }


class AerotechConnection(PyDMConnection):
    ADDRESS_FORMAT = "ensemble://<host>[:<port>][/@poll_rate]/<parameter>"

    def __init__(self, channel, address, protocol=None, parent=None):
        super().__init__(channel, address, protocol, parent)
        self.app = QApplication.instance()
        self._closed = False

        self.addr_info = parse_address(address)
        self.host = self.addr_info['host']
        self.port = self.addr_info['port']
        self.poll_rate = self.addr_info['poll_rate']
        self.parameter = self.addr_info['parameter']

        self.client = get_client(self.host, self.port, loop=None)
        self.add_listener(channel)

        data_cls = self.addr_info['data_class']
        self.poller = data_cls(self, self.client, self.parameter,
                               poll_rate=self.poll_rate)
        self.poller.new_data_signal.connect(self.emit_data,
                                            Qt.QueuedConnection)
        self.poller.new_severity_signal.connect(self.emit_severity,
                                                Qt.QueuedConnection)

        self.metadata_timer = QTimer()
        self.metadata_timer.setInterval(1000)
        self.metadata_timer.timeout.connect(self.emit_metadata)
        self.metadata_timer.start()

    def emit_metadata(self):
        self.emit_access_state()
        self.emit_connection_state(self.client.comm is not None)
        if isinstance(self.poller, WriteOnlyParameter):
            # TODO: necessary for pydmpushbutton
            self.emit_data(0)

    @pyqtSlot(object)
    def emit_data(self, new_data):
        if new_data is not None:
            self.new_value_signal[type(new_data)].emit(new_data)

    @pyqtSlot(int)
    def emit_severity(self, severity):
        self.new_severity_signal.emit(severity)

    def emit_access_state(self):
        no_access = ((is_pydm_app() and self.app.is_read_only())
                     or not self.poller.writable)
        self.write_access_signal.emit(not no_access)

    def emit_connection_state(self, comm):
        self.connection_state_signal.emit(comm is not None)

    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    @pyqtSlot(np.ndarray)
    def put_value(self, new_val):
        if is_pydm_app() and self.app.is_read_only():
            return
        elif self._closed:
            return

        try:
            self.poller.write(new_val)
        except Exception as e:
            logger.error("Unable to put %s to %s.  Exception: %s",
                         new_val, self.address, str(e))

    def add_listener(self, channel):
        super().add_listener(channel)

        # If the channel is used for writing to PVs, hook it up to the 'put'
        # methods.
        if channel.value_signal is None:
            return

        for dtype in (str, int, float, np.ndarray):
            try:
                channel.value_signal[dtype].connect(self.put_value,
                                                    Qt.QueuedConnection)
            except KeyError:
                pass

    def remove_listener(self, channel):
        super().remove_listener(channel)

        if channel.value_signal is None:
            return

        for dtype in (str, int, float, np.ndarray):
            try:
                channel.value_signal[dtype].disconnect(self.put_value)
            except (TypeError, KeyError):
                pass

    def close(self):
        super().close()
        self._closed = True
        self.poller.requestInterruption()
        self.client.requestInterruption()


class AerotechPlugin(PyDMPlugin):
    protocol = "ensemble"
    connection_class = AerotechConnection
