import sys
import asyncio
import logging

import aerotech


async def test(host, port):
    # comm = EnsembleComm(host, port)
    comm = aerotech.EnsembleDoCommand(host, port)
    data = await comm.write_read('AXISSTATUS(@0)')
    value = await comm.read_drive_info()
    print('drive info {!r}'.format(value))
    data_points = 100
    # value = await comm.scope_start(data_points=data_points, period_ms=100)
    data = await comm.get_scope_data(data_points, ScopeData.program_counter)
    # data = await comm.get_scope_data(data_points, ScopeData.position_feedback)
    print('data', data)


if __name__ == '__main__':
    try:
        host = sys.argv[1]
    except IndexError:
        host = 'moc-b34-mc02.slac.stanford.edu'

    logging.basicConfig()
    aerotech.logger.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(host, port=8000))
    loop.close()
