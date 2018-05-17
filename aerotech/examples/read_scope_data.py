import sys
import asyncio
import logging

import aerotech


async def scope_reader(host, comm_port, scope_port, *, acquire=False):
    comm = aerotech.EnsembleDoCommand(host, comm_port)
    await comm.check_program_status()

    if acquire:
        data_points = 1000
        await comm.scope_start(data_points=data_points, period_ms=10)
        await comm.scope_wait()

    scopereader = aerotech.ScopeDataReader(comm, host=host, port=scope_port)
    data = await scopereader.read_data()
    print('data', data)


if __name__ == '__main__':
    try:
        host = sys.argv[1]
    except IndexError:
        host = 'moc-b34-mc02.slac.stanford.edu'
        # host = 'moc-b34-mc08.slac.stanford.edu'

    logging.getLogger('aerotech').setLevel(logging.DEBUG)

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(scope_reader(host, comm_port=8000,
                                         scope_port=8001))
    loop.close()
