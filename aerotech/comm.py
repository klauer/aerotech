import logging
import asyncio

from .const import (EOS_CHAR, ACK_CHAR, NAK_CHAR, FAULT_CHAR, TIMEOUT_CHAR,
                    Drives, Variables, Commands, ScopeData, ScopeStatusType,
                    DataCollectionMask, TaskState, AxisStatus, AxisFault)
from .exceptions import (FailureResponseException, FaultResponseException,
                         TimeoutResponseException, UnknownResponseException,
                         WriteFailureException,
                         )


logger = logging.getLogger(__name__)


def _normalize_axis(axis):
    if isinstance(axis, str):
        return axis
    elif isinstance(axis, int):
        return '@{}'.format(axis)
    raise ValueError('Unexpected axis type (specify name or number)')


class EnsembleGlobal:
    def __init__(self, comm, index, *, check=False):
        self._comm = comm
        self._index = index
        self.check = check

    async def get(self):
        '''Get the value of the global variable'''
        ...

    async def set(self, value, *, check=None):
        '''Set the value of the global variable'''
        ...

    @property
    def index(self):
        '''Global variable index'''
        return self._index

    def __repr__(self):
        return '{}(index={})'.format(type(self).__name__, self._index)


class EnsembleGlobalInt(EnsembleGlobal):
    '''Ensemble IGLOBAL'''
    async def get(self):
        data = await self._comm.write_read('IGLOBAL({})'.format(self._index))
        return int(data)

    async def set(self, value: int, *, check=None):
        if check is None:
            check = self.check

        value = int(value)
        await self._comm.write_read('IGLOBAL({}) = {}'.format(self._index, value))
        if self.check:
            read_value = await self.get()
            if read_value != value:
                raise WriteFailureException(value, read_value)
            return read_value


class EnsembleGlobalDouble(EnsembleGlobal):
    '''Ensemble DGLOBAL'''
    float_tolerance = 0.0001

    async def get(self):
        data = await self._comm.write_read('DGLOBAL({})'.format(self._index))
        return float(data)

    async def dglobal_set(self, value: float, *, check=None):
        if check is None:
            check = self.check

        value = float(value)
        await self._comm.write_read('DGLOBAL({}) = {}'.format(self._index, value))
        if check:
            read_value = await self.get()
            if abs(read_value - value) > self.float_tolerance:
                raise WriteFailureException(value, read_value)
            return read_value


class EnsembleComm:
    def __init__(self, host, port, *, loop=None):
        self.host = host
        self.port = int(port)
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self._reader = None
        self._writer = None
        self._dglobals = {}
        self._iglobals = {}

    async def _open_connection(self):
        if self._reader is not None:
            return

        r_w = await asyncio.open_connection(self.host, self.port,
                                            loop=self.loop)
        self._reader, self._writer = r_w

    async def close(self):
        if self._reader is None:
            return

        self._writer.close()
        self._reader = None
        self._writer = None

    async def _write(self, line):
        await self._open_connection()
        if EOS_CHAR not in line:
            line = ''.join((line, EOS_CHAR))

        self._writer.write(line.encode('latin-1'))

    async def write_read(self, line):
        await self._open_connection()
        if EOS_CHAR not in line:
            line = ''.join((line, EOS_CHAR))

        self._writer.write(line.encode('latin-1'))

        read = ''
        while EOS_CHAR not in read:
            read += (await self._reader.read(1024)).decode('latin-1')

        code, response = read[0], read[1:]
        logger.debug('Wrote: %r Read: code=%s response=%r', line, code,
                     response)
        if code == ACK_CHAR:
            return response
        elif code == NAK_CHAR:
            raise FailureResponseException(response)
        elif code == FAULT_CHAR:
            raise FaultResponseException(response)
        elif code == TIMEOUT_CHAR:
            raise TimeoutResponseException(response)

        raise UnknownResponseException(code, response)

    def iglobal(self, num) -> EnsembleGlobalInt:
        '''Get an EnsembleGlobalInt instance corresponding to an index'''
        try:
            return self._iglobals[num]
        except KeyError:
            var = EnsembleGlobalInt(self, num)
            self._iglobals[num] = var
            return var

    def dglobal(self, num) -> EnsembleGlobalDouble:
        '''Get an EnsembleGlobalDouble instance corresponding to an index'''
        try:
            return self._dglobals[num]
        except KeyError:
            var = EnsembleGlobalDouble(self, num)
            self._dglobals[num] = var
            return var

    async def get_task_state(self, task_number):
        '''Get the TaskState of a specific task number'''
        task_state = await self.write_read('TASKSTATE({})'.format(task_number))
        return TaskState(int(task_state))

    async def run_program(self, task_number, program_name):
        '''Run a program on a specific task number'''
        logger.debug('Running %r on task %s', program_name, task_number)
        await self.write_read('PROGRAM RUN {}, "{}"'
                              ''.format(task_number, program_name))

    async def stop_task(self, task_number):
        '''Stop a specific task'''
        logger.debug('Stopping task %s', task_number)
        await self.write_read('PROGRAM STOP {}'.format(task_number))

    async def ensure_task(self, task_number, program_name):
        '''Ensure a program is running on a specific task number

        If the task is already running, this will be a no-operation.
        If the task has errored, it will first be stopped.
        There is no check to see if the correct program is running.
        '''
        state = await self.get_task_state(task_number)
        if state in (TaskState.running, ):
            # Task is already running
            pass
        elif state in (TaskState.idle, TaskState.ready, TaskState.paused,
                       TaskState.done, TaskState.errored):
            if state == TaskState.errored:
                logger.debug('Task %s has errored; stopping it', task_number)
                await self.stop_task(task_number)
                await asyncio.sleep(0.1)

            await self.run_program(task_number, program_name)

    async def reset(self):
        logger.debug('Resetting')
        await self._write('RESET')

    async def commit_parameters(self, *, reset=False):
        logger.debug('Committing parameters...')
        await self.write_read('COMMITPARAMETERS')
        if reset:
            await self.reset()

    async def get_axis_status(self, axis):
        axis = _normalize_axis(axis)
        status = await self.write_read('AXISSTATUS {}'.format(axis))
        return AxisStatus(int(status))

    async def get_axis_fault_status(self, axis):
        axis = _normalize_axis(axis)
        fault = await self.write_read('AXISFAULT {}'.format(axis))
        return AxisFault(int(fault))

    async def move(self, axis_position_pairs: dict, *, speed, absolute):
        axis_pos = ('{} {}'.format(_normalize_axis(axis), position)
                    for axis, position in axis_position_pairs.items())
        cmd = 'MOVE{} {} F{}'.format('ABS' if absolute else 'INC',
                                     ' '.join(axis_pos), speed)
        logger.debug('Moving: %s', cmd)
        return await self.write_read(cmd)

    async def wait_axis_status(self, axis, flags, *, poll_period=0.01,
                               check_enabled=False):
        while True:
            status = await self.get_axis_status(axis)
            if flags in status:
                return True
            elif check_enabled and AxisStatus.Enabled not in status:
                return False

            await asyncio.sleep(poll_period)

    async def move_and_wait(self, axis_position_pairs: dict, *,
                            wait_flags=AxisStatus.InPosition, speed, absolute,
                            poll_period=0.01):
        await self.move(axis_position_pairs, speed=speed, absolute=absolute)
        for axis in axis_position_pairs:
            logger.debug('Waiting on axis %s', axis)
            await self.wait_axis_status(axis, wait_flags, check_enabled=True,
                                        poll_period=poll_period)

    async def home(self, axes, wait_flags=AxisStatus.InPosition,
                   poll_period=0.01):
        if isinstance(axes, str):
            axes = [axes]
        await self.write_read('HOME {}'.format(' '.join(axes)))
        for axis in axes:
            logger.debug('Waiting on axis %s', axis)
            await self.wait_axis_status(axis, wait_flags, check_enabled=True,
                                        poll_period=poll_period)


class EnsembleDoCommand(EnsembleComm):
    '''Ensemble running script doCommand.ab/bcx as task #1'''

    task_number = 1
    program_name = 'doCommand.bcx'

    _int_nums = [Variables.int_arg1, Variables.int_arg2, Variables.int_arg3,
                 Variables.int_arg4,
                 ]
    _double_nums = [Variables.double_arg1, Variables.double_arg2,
                    Variables.double_arg3, Variables.double_arg4,
                    Variables.double_arg5, Variables.double_arg6,
                    Variables.double_arg7, Variables.double_arg8,
                    Variables.double_arg9,
                    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._int_args = [EnsembleGlobalInt(self, idx)
                          for idx in self._int_nums]
        self._double_args = [EnsembleGlobalDouble(self, idx)
                             for idx in self._double_nums]

    async def check_program_status(self):
        '''Start doCommand.bcx if not already running'''
        await self.ensure_task(self.task_number, self.program_name)
        return True

    async def write_command(self, command: Commands, *, wait=True,
                            int_args=None, double_args=None):
        if int_args is not None:
            for arg, value in zip(self._int_args, int_args):
                await arg.set(value)

        if double_args is not None:
            for arg, value in zip(self._double_args, double_args):
                await arg.set(value)

        cmd_arg = self.iglobal(Variables.command)
        await cmd_arg.set(command, check=False)

        if wait and command != Commands.do_trajectory:
            while True:
                value = await cmd_arg.get()
                if value == -command:
                    break
                await asyncio.sleep(0.001)

    async def read_drive_info(self):
        await self.write_command(Commands.drive_info)
        drive = await self._int_args[0].get()
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
        max_points = await self.get_scope_max_points()
        allocated = await self.get_scope_points_allocated()
        collected = await self.get_scope_points_collected()
        logger.debug('Scope configured with period %d ms / '
                     'collected %d allocated: %d of max %d',
                     period_ms, collected, allocated, max_points)

    async def scope_stop(self):
        await self.write_command(Commands.scope_trigger,
                                 int_args=[1])

    async def get_scope_status(self, *,
                               type_=ScopeStatusType.collection_status):
        await self.write_command(Commands.scope_status, int_args=[type_])
        return await self._int_args[0].get()

    async def get_scope_max_points(self):
        return await self.get_scope_status(type_=ScopeStatusType.max_points)

    async def get_scope_points_allocated(self):
        return await self.get_scope_status(
            type_=ScopeStatusType.points_allocated)

    async def get_scope_points_collected(self):
        return await self.get_scope_status(
            type_=ScopeStatusType.points_collected)

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
        allocated = await self.get_scope_points_allocated()
        while True:
            full_status = await self.get_friendly_scope_status()
            if DataCollectionMask.done in full_status:
                break
            collected = await self.get_scope_points_collected()
            if DataCollectionMask.aborted in full_status:
                logger.warning('Data collection aborted; collected %d of %d',
                               collected, allocated)
                break
            elif DataCollectionMask.active not in full_status:
                logger.warning('Data collection no longer active; '
                               'collected %d of %d', collected, allocated)
                break

            logger.debug('Scope collected %d of %d', collected, allocated)
            await asyncio.sleep(poll_period)

    async def get_scope_data(self, data_points, data_key: ScopeData):
        '''Copy up to data_points of scope data from the ScopeData key

        Note: with the modified doCommand provided in this repository, we can
        get more data out in parallel and significantly increase the
        throughput.

        For that, see: fast_get_scope_data
        '''
        data = []

        # set up the first point to read out
        await self.write_command(Commands.scope_data,
                                 int_args=[data_key, 0],
                                 double_args=[0.0])

        data_key_var, data_point_var = self._int_args[:2]
        data_arg = self._double_args[0]

        # then iterate over all to read them (TODO duplicate first point)
        for i in range(data_points):
            await data_point_var.set(i)
            await self.write_command(Commands.scope_data)
            data.append(await data_arg.get())
        return data

    async def fast_get_scope_data(self, data_points, data_key: ScopeData):
        data = []

        # set up the first point to read out
        # args (scope_data_key, start_index, readout_points_per_command)
        max_points = len(self._double_args)
        await self.write_command(
            Commands.fast_scope_data,
            int_args=[data_key, 0, max_points],
            double_args=[0.0],
        )

        data_key_var, data_point_var, num_points_var = self._int_args[:3]

        for i in range(0, data_points, max_points):
            num_to_read = min((max_points, data_points - i))
            data_args = self._double_args[:num_to_read]
            await data_point_var.set(i)
            if num_to_read != max_points:
                await num_points_var.set(num_to_read)
            await self.write_command(Commands.fast_scope_data)
            data.extend([await dvar.get() for dvar in data_args])
        return data
