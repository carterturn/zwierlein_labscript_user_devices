'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py
import numpy as np

class TeensyDACInterface(object):
    def __init__(self, serial_number):
        global serial; import serial
        import serial.tools.list_ports

        port_gen = serial.tools.list_ports.grep('USB VID:PID=16C0:0483 SER=' + serial_number)

        com_port = next(port_gen, None)
        if com_port is None:
            raise RuntimeError('Unable to find Teensy DAC with serial number ' + serial_number)
        if next(port_gen, None) is not None:
            raise RuntimeError('Found multiple Teensy DACs with serial number ' + serial_number)

        self.timeout = 0.1
        self.conn = serial.Serial(com_port.device, 10000000, timeout=self.timeout)

        self.clear()
        if not self.clear():
            self.conn.close()
            raise RuntimeError('Unable to communicate with Teensy DAC')

    def clear(self):
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

    def add(self, value):
        '''Sends 'add' command with the given parameters
        Returns response, throws serial exception on disconnect.'''
        self.conn.write('add:{:e}\n'.format(value).encode())
        return self.conn.read_until(b'> ')

    def add_batch(self, commands):
        '''Sends 'adb' command to write all commands in commands list. Returns response.'''
        self.conn.write('adb:{:d}\n'.format(len(commands)).encode())
        ready = self.conn.read_until(b'\n')
        if ready != b'ready\r\n':
            return ready
        self.conn.write(commands.tobytes())
        return self.conn.read_until(b'> ')

    def manual(self, val_V):
        '''Sends 'man' command with the given parameters
        Returns response, throws serial exception on disconnect.'''
        self.conn.write('man:{:e}\n'.format(val_V).encode())
        return self.conn.read_until(b'> ')

    def status(self):
        '''Sends 'stt' command
        Returns response, throws serial exception on disconnect.'''
        self.conn.write('stt\n'.encode())
        return self.conn.read_until(b'> ')

    def close(self):
        self.conn.close()

class TeensyDACWorker(Worker):
    def init(self):
        self.intf = TeensyDACInterface(self.serial_number)

    def program_manual(self, values):
        self.intf.abort()
        self.intf.manual(values['output'])

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        final_values = {}
        final_values['dac_data'] = {}

        resp = self.intf.abort()
        if resp != b'> ':
            raise RuntimeError('TeensyDAC abort returned {}'.format(resp))
        resp = self.intf.clear()
        if resp != b'> ':
            raise RuntimeError('TeensyDAC clear returned {}'.format(resp))

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            commands = np.array(group['dac_data'], dtype='<u2')
            print(len(commands))
            resp = self.intf.add_batch(commands)
            if resp != b'> ':
                raise RuntimeError('TeensyDAC add_batch returned {}'.format(resp))

        resp = self.intf.run()
        if resp != b'> ':
            raise RuntimeError('TeensyDAC run returned {}'.format(resp))

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
