'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs_workers import TeensyDACInterface
import numpy as np
from timeit import default_timer as timer

intf = TeensyDACInterface('/dev/ttyACM0')
intf.clear()

command = (0.1, 0.5, 1)
commands = [command] * 42000
commands = np.array(commands, dtype=[('start val', float), ('stop val', float), ('sweep time', float)])

t_start = timer()

resp = intf.add_batch(commands)
print(resp.decode())

t_end = timer()

print(t_end - t_start)

intf.close()
