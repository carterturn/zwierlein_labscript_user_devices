from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py

class AD9914PicoInterface(object):
    def __init__(self, com_port):
        global serial; import serial

        self.timeout = 0.1
        self.conn = serial.Serial(com_port, 115200, timeout=self.timeout)

        self.clear()
        if not self.clear():
            raise RuntimeError('Unable to communicate with AD9914 Pico')

    def clear(self):
        '''Sends 'cls' command, which clears the currently stored run.
        Returns true if response is the expected prompt (false otherwise).'''
        self.conn.write(b'cls\n')
        return self.conn.read_until(b'> ')

    def abort(self):
        '''Sends 'abt' command, which stops the current run (or does nothing if no run).
        Returns true if response is the expected prompt (false otherwise).'''
        self.conn.write(b'abt\n')
        return self.conn.read_until(b'> ')

    def run(self):
        '''Sends 'run' command, which starts the current run.
        Returns true if response is the expected prompt (false otherwise).'''
        self.conn.write(b'run\n')
        return self.conn.read_until(b'> ')

    def dump(self):
        '''Sends 'dmp' command, which dumps the currently loaded run.
        Returns the dump of the run.'''
        self.conn.write(b'dmp\n')
        return self.conn.read_until(b'> ')

    def add(self, start_freq, start_amp, stop_freq=None, stop_amp=None, sweep_time=None, trigger=True):
        '''Sends 'add' command with the given parameters
        Returns true if response is the expected prompt (false otherwise).'''
        if trigger:
            trigger = 1
        else:
            trigger = 0
        if stop_freq is None and stop_amp is None:
            self.conn.write('add:cst,{:e},cst,{:e},{:e}\n'
                            .format(start_freq, start_amp, trigger).encode())
        elif sweep_time is None:
            raise RuntimeError('Error AD9914 Pico attempting to sweep with no sweep time')
        elif stop_amp is None:
            self.conn.write('add:lin,{:e},{:e},cst,{:e},{:e},{:e}\n'
                            .format(start_freq, stop_freq, start_amp, sweep_time, trigger)
                            .encode())
        elif stop_freq is None:
            self.conn.write('add:cst,{:e},lin,{:e},{:e},{:e},{:e}\n'
                            .format(start_freq, start_amp, stop_amp, sweep_time, trigger)
                            .encode())
        else:
            self.conn.write('add:lin,{:e},{:e},lin,{:e},{:e},{:e},{:e}\n'
                            .format(start_freq, stop_freq, start_amp, stop_amp, sweep_time, trigger)
                            .encode())
        return self.conn.read_until(b'> ')

    def close(self):
        self.conn.close()

class AD9914PicoWorker(Worker):
    def init(self):
        self.intf = AD9914PicoInterface(self.com_port)

    def program_manual(self, values):
        self.intf.abort()
        self.intf.clear()

        self.intf.add(values['output']['freq'], values['output']['amp'], trigger=False)

        self.intf.run()

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        final_values = {}
        final_values['dds_data'] = {}

        self.intf.clear()

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            commands = group['dds_data']
            for command in commands:
                if command['sweep']:
                    self.intf.add(command['start freq'], command['start amp'],
                                  command['stop freq'], command['stop amp'],
                                  command['sweep time'], command['trigger'])
                else:
                    self.intf.add(command['start freq'], command['start amp'],
                                  trigger=command['trigger'])

        self.intf.run()

        return {}

    def transition_to_manual(self):
        return True

    def abort_buffered(self):
        self.intf.abort()
        return True

    def abort_transition_to_buffered(self):
        self.intf.abort()
        return True

    def shutdown(self):
        self.intf.close()
