from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py

class GlassPlateRotatorWorker(Worker):
    def init(self):
        global serial; import serial
        self.conn = serial.Serial(self.com_port, baudrate=9600, timeout=0.1)

    def program_rotator(self, modes, positions_0, positions_1):
        # Apply inversions
        if self.inverted is not None:
            positions_0 = [p if not i else -p for p, i in zip(positions_0, self.inverted)]
            positions_1 = [p if not i else -p for p, i in zip(positions_1, self.inverted)]

        # Set mode for each channel
        mode_set_msg = '<'
        for i, mode in enumerate(modes):
            mode_set_msg += 'CH{}MODE:'.format(i)
            if mode == 'calibration':
                mode_set_msg += '2'
            elif mode == 'static':
                mode_set_msg += '1'
            elif mode == 'motion':
                mode_set_msg += '0'
            mode_set_msg += ';'
        mode_set_msg = mode_set_msg[:-1]
        mode_set_msg += '>'
        self.conn.write(mode_set_msg.encode())

        # Set position zero (TTL low) for each channel
        set_0_msg = '<'
        for i, position_0 in enumerate(positions_0):
            set_0_msg += 'CH{}POS0:'.format(i)
            set_0_msg += str(position_0)
            set_0_msg += ';'
        set_0_msg = set_0_msg[:-1]
        set_0_msg += '>'
        self.conn.write(set_0_msg.encode())

        # Set position one (TTL high) for each channel
        set_1_msg = '<'
        for i, position_1 in enumerate(positions_1):
            set_1_msg += 'CH{}POS1:'.format(i)
            set_1_msg += str(position_1)
            set_1_msg += ';'
        set_1_msg = set_1_msg[:-1]
        set_1_msg += '>'
        self.conn.write(set_1_msg.encode())

    def program_manual(self, values):
        modes = []
        positions_0 = []
        positions_1 = []
        for channel_name in self.channel_names:
            modes.append(values[channel_name]['mode'])

            if values[channel_name]['first'] == 'upper':
                positions_0.append(int(values[channel_name]['pos_upper']))
                positions_1.append(int(values[channel_name]['pos_lower']))
            else:
                positions_0.append(int(values[channel_name]['pos_lower']))
                positions_1.append(int(values[channel_name]['pos_upper']))

        self.program_rotator(modes, positions_0, positions_1)

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            positions = group['rotator_data']

            self.program_rotator(['motion' for c in self.channel_names],
                                 [positions['{} upper'.format(c)][0] for c in self.channel_names],
                                 [positions['{} lower'.format(c)][0] for c in self.channel_names])

        return {}

    def transition_to_manual(self):
        return True

    def abort_buffered(self):
        return True

    def abort_transition_to_buffered(self):
        return True

    def shutdown(self):
        self.conn.close()
