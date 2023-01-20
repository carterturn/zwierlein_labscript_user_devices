from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py

class AD9914PicoInterface(object):
    def __init__(self, com_port):
        global serial; import serial

        self.conn = serial.Serial(com_port, 115200, timeout=0.1)

        self.clear()
        if not self.clear():
            raise RunetimeError('Unable to communicate with AD9914 Pico')

    def clear(self):
        '''Sends 'cls' command, which clears the currently stored run.
        Returns true if response is the expected prompt (false otherwise).'''
        self.conn.write(b'cls\n')
        return self.conn.readlines()[-1] == '> '

    def abort(self):
        '''Sends 'abt' command, which stops the current run (or does nothing if no run).
        Returns true if response is the expected prompt (false otherwise).'''
        self.conn.write(b'abt\n')
        return self.conn.readlines()[-1] == '> '

    def run(self):
        '''Sends 'run' command, which starts the current run.
        Returns true if response is the expected prompt (false otherwise).'''
        self.conn.write(b'run\n')
        return self.conn.readlines()[-1] == '> '

    def dump(self):
        '''Sends 'dmp' command, which dumps the currently loaded run.
        Returns the dump of the run.'''
        self.conn.write(b'dmp\n')
        return self.conn.readlines()[:-1]

    def add(self, start_freq, start_amp, stop_freq=None, stop_amp=None, sweep_time=None, trigger=True):
        '''Sends 'add' command with the given parameters
        Returns true if response is the expected prompt (false otherwise).'''
        if trigger:
            trigger = 1
        else:
            trigger = 0
        if stop_freq is None and stop_amp is None:
            self.conn.write(b'add:cst,{},cst,{},{}\n'.format(start_freq, start_amp), trigger)
        elif sweep_time is None:
            raise RunetimeError('Error AD9914 Pico attempting to sweep with no sweep time')
        elif stop_amp is None:
            self.conn.write(b'add:lin,{},{},cst,{},{},{}\n'
                            .format(start_freq, stop_freq, start_amp, sweep_time, trigger))
        elif stop_freq is None:
            self.conn.write(b'add:cst,{},lin,{},{},{},{}\n'
                            .format(start_freq, start_amp, stop_amp, sweep_time, trigger))
        else:
            self.conn.write(b'add:lin,{},{},lin,{},{},{},{}\n'
                            .format(start_freq, stop_freq, start_amp, stop_amp, sweep_time, trigger))
        return self.conn.readlines()[-1] == '> '

    def close(self):
        self.conn.close()

class AD9914PicoWorker(Worker):
    def init(self):
        self.intf = AD9914PicoInterface(self.com_port)

    def program_manual(self, values):
        self.intf.abort()
        if not self.intf.clear():
            return False

        self.intf.add(values['channel 0']['freq'], values['channel 0']['amp'])

        return self.intf.run()

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        final_values = {}
        final_values['dds_data'] = {}

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            commands = group['dds_data']
            for command in commands:
                if command['sweep']:
                    if not self.intf.add(command['start freq'], command['start amp'],
                                         command['stop freq'], command['stop amp'],
                                         command['sweep time'], command['trigger']):
                        return False
                else:
                    if not self.intf.add(command['start freq'], command['start amp'],
                                         trigger=command['trigger']):
                        return False

        return True

    def transition_to_manual(self):
        return True

    def abort_buffered(self):
        return self.intf.abort()

    def abort_transition_to_buffered(self):
        return self.intf.abort()

    def shutdown(self):
        self.intf.close()
