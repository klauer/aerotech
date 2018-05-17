import sys
import asyncio
import logging

import aerotech


async def test(host, port):
    comm = aerotech.EnsembleDoCommand(host, port)

    await comm.check_program_status()
    data_points = 1000
    await comm.scope_start(data_points=data_points, period_ms=10)
    await comm.scope_wait()
    # data = await comm.get_scope_data(data_points, ScopeData.program_counter)
    # data = await comm.get_scope_data(data_points,
    #                                  aerotech.ScopeData.position_feedback)
    data = await comm.fast_get_scope_data(data_points,
                                          aerotech.ScopeData.position_feedback)
    print('data', data)

if __name__ == '__main__':
    try:
        host = sys.argv[1]
    except IndexError:
        host = 'moc-b34-mc02.slac.stanford.edu'
        # host = 'moc-b34-mc08.slac.stanford.edu'

    aerotech.logger.setLevel(logging.DEBUG)

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(host, port=8000))
    loop.close()
