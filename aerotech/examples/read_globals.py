import sys
import asyncio
import logging

import aerotech


async def test(host, port):
    comm = aerotech.EnsembleComm(host, port)
    global1 = comm.iglobal(1)
    value = await global1.get()
    print('{!r} = {}'.format(global1, value))

    dglobal1 = comm.dglobal(1)
    value = await dglobal1.get()
    print('{!r} = {}'.format(dglobal1, value))


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
