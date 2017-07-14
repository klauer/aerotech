import logging
import asyncio

from .const import (EOS_CHAR, ACK_CHAR, NAK_CHAR, FAULT_CHAR, TIMEOUT_CHAR,
                    Drives, Variables, Commands, ScopeData,
                    DataCollectionMask)
from .exceptions import (FailureResponseException, FaultResponseException,
                         TimeoutResponseException, UnknownResponseException,
                         WriteFailureException,
                         )


logger = logging.getLogger(__name__)


class EnsembleComm:
    float_tolerance = 0.0001

    def __init__(self, host, port, *, loop=None):
        self.host = host
        self.port = int(port)
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self._reader = None
        self._writer = None

    async def _open_connection(self):
        if self._reader is not None:
            return

        r_w = await asyncio.open_connection(self.host, self.port,
                                            loop=self.loop)
        self._reader, self._writer = r_w

    async def write_read(self, line):
        await self._open_connection()

        if EOS_CHAR not in line:
            line = ''.join((line, EOS_CHAR))

        logger.debug('Writing %r', line)
        self._writer.write(line.encode('latin-1'))

        read = ''
        while EOS_CHAR not in read:
            read += (await self._reader.read(1024)).decode('latin-1')

        code, response = read[0], read[1:]
        logger.debug('Read code=%s response=%r', code, response)
        if code == ACK_CHAR:
            return response
        elif code == NAK_CHAR:
            raise FailureResponseException(response)
        elif code == FAULT_CHAR:
            raise FaultResponseException(response)
        elif code == TIMEOUT_CHAR:
            raise TimeoutResponseException(response)

        raise UnknownResponseException(code, response)

    async def iglobal_get(self, num):
        data = await self.write_read('IGLOBAL({})'.format(num))
        return int(data)

    async def iglobal_set(self, num, value: int, *, check=False):
        value = int(value)
        await self.write_read('IGLOBAL({}) = {}'.format(num, value))
        if check:
            read_value = await self.iglobal_get(num)
            if read_value != value:
                raise WriteFailureException(value, read_value)
            return read_value

    async def dglobal_get(self, num):
        data = await self.write_read('DGLOBAL({})'.format(num))
        return float(data)

    async def dglobal_set(self, num, value: float, *, check=False):
        value = float(value)
        await self.write_read('DGLOBAL({}) = {}'.format(num, value))
        if check:
            read_value = await self.dglobal_get(num)
            if abs(read_value - value) > self.float_tolerance:
                raise WriteFailureException(value, read_value)
            return read_value


class EnsembleDoCommand(EnsembleComm):
    '''Ensemble running script doCommand.ab/bcx as task #1'''

    _int_vars = [Variables.int_arg1, Variables.int_arg2, Variables.int_arg3,
                 Variables.int_arg4,
                 ]
    _double_vars = [Variables.double_arg1, Variables.double_arg2,
                    Variables.double_arg3, Variables.double_arg4,
                    Variables.double_arg5, Variables.double_arg6,
                    Variables.double_arg7, Variables.double_arg8,
                    Variables.double_arg9,
                    ]

    async def check_script_status(self):
        ...
        # start doCommand.bcx if not already running

    async def write_command(self, command: Commands, *, wait=True,
                            int_args=None, double_args=None):
        if int_args is not None:
            for var, value in zip(self._int_vars, int_args):
                await self.iglobal_set(var, value)

        if double_args is not None:
            for var, value in zip(self._double_vars, double_args):
                await self.dglobal_set(var, value)

        await self.iglobal_set(Variables.command, command, check=False)

        if wait and command != Commands.do_trajectory:
            while True:
                value = await self.iglobal_get(Variables.command)
                if value == -command:
                    break
                await asyncio.sleep(0.01)

    async def read_drive_info(self):
        await self.write_command(Commands.drive_info)
        drive = await self.iglobal_get(Variables.int_arg1)
        try:
            return Drives(drive)
        except TypeError:
            logger.error('Unknown drive type: %d', drive)
            return drive

    async def scope_start(self, data_points, period_ms):
        await self.scope_stop()
        await self.write_command(Commands.scope_buffer,
                                 int_args=[data_points])
        await self.write_command(Commands.scope_trigger_period,
                                 int_args=[period_ms])
        await self.write_command(Commands.scope_trigger,
                                 int_args=[0])

    async def scope_stop(self):
        await self.write_command(Commands.scope_trigger,
                                 int_args=[1])

    async def get_scope_status(self):
        await self.write_command(Commands.scope_status)
        return await self.iglobal_get(Variables.int_arg1)

    async def get_friendly_scope_status(self):
        status = await self.get_scope_status()
        info = []
        for bit in range(8):
            try:
                info.append(DataCollectionMask((1 << bit) & status))
            except ValueError:
                ...
        return info

    async def scope_wait(self, *, poll_period=0.1):
        while True:
            full_status = await self.get_friendly_scope_status()
            if DataCollectionMask.done in full_status:
                break
            await asyncio.sleep(poll_period)

    async def get_scope_data(self, data_points, data_key: ScopeData):
        await self.scope_wait()
        await self.write_command(Commands.scope_data, int_args=[data_key])
        data = []
        await self.write_command(Commands.scope_data,
                                 int_args=[data_key, 0],
                                 double_args=[0.0])

        data_key_var, data_point_var = self._int_vars[:2]
        data_var = self._double_vars[0]
        for i in range(data_points):
            await self.iglobal_set(data_point_var, i)
            await self.write_command(Commands.scope_data)
            data.append(await self.dglobal_get(data_var))
        return data


def main(host, port):
    async def main_test():
        # comm = EnsembleComm(host, port)
        comm = EnsembleDoCommand(host, port)
        # data = await comm.write_read('AXISSTATUS(@0)')
        value = await comm.read_drive_info()
        print('drive info {!r}'.format(value))
        data_points = 100
        # value = await comm.scope_start(data_points=data_points, period_ms=100)
        data = await comm.get_scope_data(data_points, ScopeData.program_counter)
        # data = await comm.get_scope_data(data_points, ScopeData.position_feedback)
        print('data', data)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_test())
    loop.close()


if __name__ == '__main__':
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    main(host='moc-b34-mc02.slac.stanford.edu', port=8000)
