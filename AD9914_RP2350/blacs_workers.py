'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py

class AD9914RP2350Interface(object):
    def __init__(self, com_port):
        global serial; import serial

        self.timeout = 0.1
        self.conn = serial.Serial(com_port, 10000000, timeout=self.timeout)

        self.clear()
        if not self.clear():
            raise RuntimeError('Unable to communicate with AD9914 Pico')

    def manual(self):
        '''Sends 'cls' command, which clears the currently stored run.
        Returns response, throws serial exception on disconnect.'''
        self.conn.write(b'cls\n')
        return self.conn.read_until(b'> ')

    def abort(self):
        '''Sends 'abt' command, which stops the current run (or does nothing if no run).
        Returns response, throws serial exception on disconnect.'''
        self.conn.write(b'abt\n')
        return self.conn.read_until(b'> ')

    def run(self):
        '''Sends 'run' command, which starts the current run.
        Returns response, throws serial exception on disconnect.'''
        self.conn.write(b'run\n')
        return self.conn.read_until(b'> ')

    def dump(self):
        '''Sends 'dmp' command, which dumps the currently loaded run.
        Returns the dump of the run.'''
        self.conn.write(b'dmp\n')
        return self.conn.read_until(b'> ')

    def set_batch(self, commands):
        '''Sends 'set' commands for each command in commands list. Returns response.'''
        idx = 0
        for command in commands:
            trigger = command['trigger']
            start_freq = command['start freq']
            start_amp = command['start amp']
            stop_freq = command['stop freq']
            stop_amp = command['stop amp']
            sweep_time = command['sweep time']
            if trigger:
                trigger = 1
            else:
                trigger = 0
            if not command['sweep']:
                self.conn.write('set {:d} {:e} {:e} 0 {:d}\n'
                                .format(idx, start_freq, start_amp, trigger).encode())
                print('set {:d} {:e} {:e} 0 {:d}\n'
                      .format(idx, start_freq, start_amp, trigger))
            else:
                self.conn.write('ser {:d} {:e} {:e} {:e} {:e} 0 0 {:e} {:d}\n'
                                .format(idx, start_freq, stop_freq, start_amp, stop_amp,
                                        sweep_time, trigger).encode())
                print('ser {:d} {:e} {:e} {:e} {:e} 0 0 {:e} {:d}\n'
                      .format(idx, start_freq, stop_freq, start_amp, stop_amp,
                              sweep_time, trigger))
        resp = b''
        for command in commands:
            resp += self.conn.read_until(b'> ')

        self.conn.write('sec {:d}\n'.format(idx+1).encode())
        print('sec {:d}\n'.format(idx+1))
        return resp

    def close(self):
        self.conn.close()

class AD9914RP2350Worker(Worker):
    def init(self):
        self.intf = AD9914RP2350Interface(self.com_port)

    def program_manual(self, values):
        self.intf.abort()

        self.intf.manual(values['output']['freq'], values['output']['amp'], 0)

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        final_values = {}
        final_values['dds_data'] = {}

        self.intf.clear()

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            commands = group['dds_data']
            self.intf.add_batch(commands)

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
