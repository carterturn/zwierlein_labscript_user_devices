'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py

class AD9959DDSSweeperInterface(object):
    def __init__(self, com_port):
        global serial; import serial

        self.timeout = 0.1
        self.conn = serial.Serial(com_port, 10000000, timeout=self.timeout)

        version = self.get_version()
        print(f'Connected to version: {version}')

        current_status = self.status()
        print(f'Current status is {current_status}')

        self.conn.write(b'setclock 0 125000000\n')
        assert self.conn.readline().decode() == "ok"
        self.conn.write(b'setmult 4\n')
        assert self.conn.readline().decode() == "ok"

    def get_version(self):
        '''Sends 'version' command, which retrieves the Pico firmware version.
        Returns response, throws serial exception on disconnect.'''
        self.conn.write(b'version\n')
        version_str = self.conn.readline().decode()
        version = tuple(int(i) for i in version_str.split('.'))
        assert len(version) == 3
        return version

    def abort(self):
        '''Stops buffered execution immediately.'''
        self.conn.write(b'abort\n')
        assert self.conn.readline().decode() == "ok"

    def start(self):
        '''Starts buffered execution.'''
        self.conn.write(b'start\n')
        assert self.conn.readline().decode() == "ok"
    
    def get_status(self):
        '''Reads the status of the AD9959 DDS Sweeper
        Returns int status code.`'''
        self.conn.write(b'status\n')
        status_str = int(self.conn.readline().decode())
        if status_str == 0:
            return 'STOPPED'
        elif status_str == 1:
            return 'RUNNING'
        elif status_str == 2:
            return 'ABORTING'
        else:
            raise LabscriptError(f'PrawnDO invalid status, returned {status_str}')

    def get_freqs(self):
        '''Responds with a dictionary containing
        the current operating frequencies (in kHz) of various clocks.'''
        self.conn.write(b'getfreqs\n')
        freqs = {}
        while True:
            resp = self.conn.readline().decode()
            if resp == "ok":
                break
            resp = resp.split('=')
            freqs[resp[0].strip()] = int(resp[1].strip()[:-3])
        return freqs

    def set_output(self, channel, frequency, amplitude, phase):
        '''Set frequency, amplitude, and phase of a channel.'''
        self.conn.write(b'setfreq %d %f\n' % (channel, frequency))
        assert self.conn.readline().decode() == "ok"
        self.conn.write(b'setamp %d %f\n' % (channel, amplitude))
        assert self.conn.readline().decode() == "ok"
        self.conn.write(b'setphase %d %f\n' % (channel, phase))
        assert self.conn.readline().decode() == "ok"

    def set_channels(self, channels):
        '''Set number of channels to use in buffered sequence.'''
        self.conn.write(b'setchannels %d %f\n' % channels)
        assert self.conn.readline().decode() == "ok"

    def set(self, channel, addr, frequency, amplitude, phase):
        '''Set frequency, phase, and amplitude of a channel
        for address addr in buffered sequence.'''
        self.conn.write(b'set %d %d %f %f %f\n' % (channel, addr, frequency, amplitude, phase))
        assert self.conn.readline().decode() == "ok"

    def set_batch(self, channel, table):
        '''Set frequency, phase, and amplitude of a channel
        for address addr in buffered sequence.'''
        k_f = 'freq%d' % channel
        k_a = 'amp%d' % channel
        k_p = 'phase%d' % channel
        for i, row in enumerate(table):
            self.conn.write(b'set %d %d %f %f %f\n' % (channel, i, row[k_f], row[k_a], row[k_p]))
        for row in table:
	        assert self.conn.readline().decode() == "ok"

    def close(self):
        self.conn.close()

class AD9959DDSSweeperWorker(Worker):
    def init(self):
        self.intf = AD9959DDSSweeperInterface(self.com_port)

    def program_manual(self, values):
        self.intf.abort()

        for chan in values:
            chan_int = int(chan[8:])
            self.intf.set_output(chan_int, values[chan]['freq'], values[chan]['amp'], values[chan]['phase'])

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        self.final_values = initial_values

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            dds_data = group['dds_data']
            channels = set([int(n[4:]) for n in dds_data.dtype.names if n.startswith('freq')])
            for channel in channels:
                self.intf.set_batch(channel, dds_data['freq%d' % channel,
                                                      'amp%d' % channel,
                                                      'phase%d' % channel])

        self.intf.start()

        return {}

    def transition_to_manual(self):
        if self.final_values:
            self.program_manual(self.final_values)
        return True

    def abort_buffered(self):
        return self.transition_to_manual()

    def abort_transition_to_buffered(self):
        return self.transition_to_manual()

    def shutdown(self):
        self.intf.close()
