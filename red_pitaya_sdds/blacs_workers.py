'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py
from user_devices.red_pitaya_sdds.labscript_devices import RedPitayaSDDSChannel
import numpy as np

class RedPitayaSDDSInterface(object):
    def __init__(self, ip):
        global socket; import socket

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((ip, 5025))

        if not self.abort('A') or not self.abort('B'):
            raise RuntimeError('Failed to connect to and stop Red Pitaya SDDS')

    def _scpi_read(self, node_list):
        return ':'.join(node_list) + '?' + '\n'

    def _scpi_readline(self):
        d = b''
        while len(d) == 0 or int(d[-1]) != ord('\n'):
            d += self.conn.recv(1024)
        return d.decode()

    def _scpi_write(self, node_list, args):
        return ':'.join(node_list) + ' ' + args + '\n'

    def _encode_sweeps(self, sweeps):
        bytes = sweeps.tobytes()

        bytes = bytes.replace(b'\\', b'\\\\')
        bytes = bytes.replace(b'\0', b'\\0')
        bytes = bytes.replace(b'\n', b'\\n')
        bytes = bytes.replace(b';', b'\\t')
        bytes = bytes.replace(b' ', b'\\s')

        return bytes
        
    def abort(self, chan):
        '''Sends 'STOP' and 'RESET' command, which stops any current output.
        Returns True if state is (starts with) 'stopped', False otherwise.'''
        self.conn.send(self._scpi_write(['DDS', chan, 'CONT'], 'STOP').encode())
        self.conn.send(self._scpi_write(['DDS', chan, 'CONT'], 'RESET').encode())
        self.conn.send(self._scpi_read(['DDS', chan, 'CONT']).encode())
        resp = self._scpi_readline()
        return resp.startswith('stopped')

    def run(self, chan):
        '''Sends 'START' command, which starts the current run.
        Returns True if state (starts with) 'running', False otherwise.'''
        self.conn.send(self._scpi_write(['DDS', chan, 'CONT'], 'START').encode())
        self.conn.send(self._scpi_read(['DDS', chan, 'CONT']).encode())
        resp = self._scpi_readline()
        return resp.startswith('running')

    def trig(self, chan):
        '''Software-triggers channel.'''
        self.conn.send(self._scpi_write(['DDS', chan, 'TRIG'], '1').encode())
        self.conn.send(self._scpi_write(['DDS', chan, 'TRIG'], '0').encode())
        return

    def add_batch(self, chan, commands):
        '''Writes commands to a channel.
        Returns True if length is updated correctly.'''
        length = len(commands)
        self.conn.send(self._scpi_write(['DDS', chan, 'LEN'], str(length)).encode())
        if length > 0:
	        data = (':'.join(['DDS', chan, 'DAT']).encode()
    	            + b' ' + self._encode_sweeps(commands) + b'\n')
	        self.conn.send(data)
        self.conn.send(self._scpi_read(['DDS', chan, 'LEN']).encode())
        resp = self._scpi_readline()
        return int(resp) == length

    def status(self, chan):
        '''Returns (DMA) status.'''
        self.conn.send(self._scpi_read(['DDS', chan, 'CONT']).encode())
        return self._scpi_readline()

    def close(self):
        self.conn.close()

class RedPitayaSDDSWorker(Worker):
    def init(self):
        self.intf = RedPitayaSDDSInterface(self.ip)

    def program_manual(self, values):
        if not self.intf.abort('A') or not self.intf.abort('B'):
            raise RuntimeError('Unable to abort during manual programming')

        # TODO
        for chan in ['A', 'B']:
            command = [(values[chan]['freq']*RedPitayaSDDSChannel.FREQ_SCALE, 0.0,
                        values[chan]['amp']*RedPitayaSDDSChannel.AMP_SCALE, 0.0, 1)]
            command_array = np.array(command, dtype=[('freq_start', '<u4'),
                                                     ('freq_step', '<i4'),
                                                     ('amp_start', '<u2'),
                                                     ('amp_step', '<i2'),
                                                     ('step_total', '<u4')])
            command_array[0]['amp_start'] |= 0x8000
            self.intf.add_batch(chan, command_array)

        if not self.intf.run('A') or not self.intf.run('B'):
            raise RuntimeError('Unable to run during manual programming')

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        final_values = {}
        final_values['dds_data'] = {}

        if not self.intf.abort('A') or not self.intf.abort('B'):
            raise RuntimeError('Failed to stop Red Pitaya SDDS')

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            commands_A = group['A'][()]
            self.intf.add_batch('A', commands_A)
            commands_B = group['B'][()]
            self.intf.add_batch('B', commands_B)

        if len(commands_A) > 0:
            if not self.intf.run('A'):
                raise RuntimeError('Failed to start Red Pitaya SDDS')
        if len(commands_B) > 0:
            if not self.intf.run('B'):
                raise RuntimeError('Failed to start Red Pitaya SDDS')

        return {}

    def transition_to_manual(self):
        return True

    def abort_buffered(self):
        return self.intf.abort('A') and self.intf.abort('B')

    def abort_transition_to_buffered(self):
        return self.intf.abort('A') and self.intf.abort('B')

    def shutdown(self):
        self.intf.close()
