# Aerotech Ensemble Python utilities

Simple asyncio-based communication module for usage with the Aerotech Ensemble.

## Features

* asyncio-based communication library
* Pure Python - no dependencies
* Fast scope data retrieval (optional; requires separate Ensemble task)
* [PyDM](https://github.com/slaclab/pydm) plugin for creating user interfaces

## Requires

* Python 3.6+
* Use motorAerotech R1-1-1 or later, preferably (upstream now includes my ``doCommand`` fixes)
* Configure socket 2 as noted below to allow this Python library to communicate.
* ``doCommand`` must be running on the Ensemble ([link](https://github.com/epics-motor/motorAerotech/blob/master/aerotechApp/src/doCommand.ab))
* For fast scope data retrieval, ``scopedata_socket3`` must be running on the Ensemble ([link](support/scopedata_socket3.ab))

## Configuration and example

(Modified instructions from https://github.com/epics-motor/motorAerotech/blob/master/aerotechApp/src/README)

- In the System->Communication->ASCII->CommandSetup Parameter, check the following items (everything else is unchecked);
    * Ethernet Socket 2
    * Always Send EOS
- In the System->Communication->Ethernet Sockets section;
	- in the ->Socket2Setup Parameter, check the "TCP server" setting.
	- Enter the IP address in the ->Socket2RemoteIPAddress Parameter
	- Leave the ->Socket2Port Parameter at the default "8000"
	- Set the ->Socket2Timeout Parameter greater than idle polling parameter of
	  the EnsembleAsynConfig() call.

Read IGLOBAL(1) with the following:

```python
import asyncio

import aerotech

async def main(host: str, port: int = 8000):
    comm = aerotech.EnsembleComm(host, port)
    global1 = comm.iglobal(1)
    value = await global1.get()
    print(f'{global1!r} = {value}')

if __name__ == "__main__":
    asyncio.run(main("ip_address"))
```

See example [script](aerotech/examples/read_globals.py)

## Fast scope data retrieval configuration

Configure Socket 3 to listen on TCP port 8001.

- In the System->Communication->Ethernet Sockets section;
	- in the ->Socket3Setup Parameter, check the "TCP server" setting.
	- Enter the IP address in the ->Socket3RemoteIPAddress Parameter
	- Leave the ->Socket3Port Parameter at the default "8001"

Download and run ``scopedata_socket3`` on the Ensemble ([link](support/scopedata_socket3.ab))

Try the example [script](aerotech/examples/read_scope_data.py)

## PyDM Configuration

The provided plugin was tested on a very old version of PyDM and is not guaranteed to work with the latest versions.
See [pydm_plugin](pydm_plugin/) for code.
