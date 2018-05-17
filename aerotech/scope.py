'''
Additional program / communication class for reading out scope data more
quickly than doCommand
'''
import logging
import asyncio

from .const import EOS_CHAR
from .exceptions import FailureResponseException
# from .comm import EnsembleDoCommand


logger = logging.getLogger(__name__)


class ScopeDataReader:
    def __init__(self, docommand, host, port, *, loop=None, task_number=2,
                 program_name='scopedata_socket2.bcx'):
        self.docommand = docommand
        self.host = host
        self.port = int(port)
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self._reader = None
        self._writer = None
        self.task_number = task_number
        self.program_name = program_name

    async def check_program_status(self):
        '''Start doCommand.bcx if not already running'''
        await self.docommand.ensure_task(self.task_number, self.program_name)

    async def _open_connection(self):
        if self._reader is not None:
            return

        r_w = await asyncio.open_connection(self.host, self.port,
                                            loop=self.loop)
        self._reader, self._writer = r_w

    async def write_read(self, command):
        await self.check_program_status()
        await self._open_connection()

        assert len(command) == 1

        self._writer.write(command)

        data = None
        mode = None
        read = ''
        while True:
            read += (await self._reader.read(1024)).decode('latin-1')

            while EOS_CHAR not in read:
                continue

            lines = read.split(EOS_CHAR)
            if not read.endswith(EOS_CHAR):
                lines = lines[:-1]
                read = lines[-1]
            else:
                read = ''

            for line in lines:
                if not line:
                    continue

                logger.debug('ScopeData line: %s', line)
                if line == 'SCOPEDATA':
                    # sent on connection
                    ...
                elif line == 'OK':
                    return True
                elif line == 'UNKNOWN':
                    raise FailureResponseException('Unknown command')
                elif line.startswith('READ POINTS'):
                    _, _, num_points = line.split(' ')
                    mode = 'points'
                    data = [[], [], [], [], []]
                elif mode == 'points':
                    if line == 'READ DONE':
                        return data
                    point, pos_cmd, pos_fbk, cur_cmd, cur_fbk = line.split(' ')
                    data[0].append(int(point))
                    data[1].append(float(pos_cmd))
                    data[2].append(float(pos_fbk))
                    data[3].append(float(cur_cmd))
                    data[4].append(float(cur_fbk))

    async def read_data(self):
        logger.debug('Reading scope data...')
        data = await self.write_read(b'R')
        logger.debug('Done')
        return data
