from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py
import numpy as np

class PrawnDOInterface(object):
    def __init__(self, com_port):
        global serial; import serial

        self.timeout = 0.1
        self.conn = serial.Serial(com_port, 10000000, timeout=self.timeout)

        self.clear()
        if not self.clear():
            raise RuntimeError('Unable to communicate with PrawnDO Pico')

    def clear(self):
        '''Sends 'cls' command, which clears the currently stored run.
        Returns response, throws serial exception on disconnect.'''
        self.conn.write(b'cls\n')
        # Note that read_until should read until the prompt, not newline
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

    def add(self, bit_set):
        '''Sends 'add' command for a single set of output bits
        Returns response, throws serial exception on disconnect.'''
        self.conn.write('add\n'.encode())
        self.conn.write('0x{:04x}\n'.format(bit_set).encode()) # Send bits as hex string
        self.conn.write('end\n'.encode())
        return self.conn.read_until(b'> ')

    def add_batch(self, bit_sets):
        '''Sends 'add' commands for each bit_set in bit_sets list. Returns response.'''
        self.conn.write('add\n'.encode())
        for bit_set in bit_sets:
            # Send each set of bits as hex string on its own line
            self.conn.write('0x{:04x}\n'.format(bit_set).encode())
        self.conn.write('end\n'.encode())
        return self.conn.read_until(b'> ')

    def close(self):
        self.conn.close()

class PrawnDOWorker(Worker):
    def init(self):
        self.intf = PrawnDOInterface(self.com_port)

    def program_manual(self, front_panel_values):
        self.intf.abort() # stop current run, if it is happening
        self.intf.clear() # clear current Pi Pico buffer

        values = np.zeros(1, dtype=np.uint16) # Make 16 bit unsigned integer
        for conn, value in front_panel_values.items():
            # "Or" each bit from the front panel into the integer
            values[0] |= value << (int(conn, 16))
        # Send to the Pi Pico
        self.intf.add(values[0])

        self.intf.run()

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        self.intf.abort() # stop current run, if it is happening
        self.intf.clear() # clear current Pi Pico buffer

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            do_table = group['do_data']
            # The data "table" contains only a single column of integers, so just convert to list
            # Need to append an initial zero, since first output occurs immediately (before trigger)
            self.intf.add_batch([0] + list(do_table))

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
