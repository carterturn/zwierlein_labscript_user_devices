from blacs_workers import AD9914PicoInterface
from timeit import default_timer as timer

intf = AD9914PicoInterface('/dev/ttyACM0')
intf.clear()

t_start = timer()

command = {'start_freq': 2e9, 'start_amp': 0.5,
           'stop_freq': 1.9e9, 'stop_amp': 0.4,
           'sweep_time': 1e-3, 'trigger': False}
commands = [command] * 100
resp = intf.add_batch(commands)
print(resp.decode())

t_end = timer()

print(t_end - t_start)

intf.close()
