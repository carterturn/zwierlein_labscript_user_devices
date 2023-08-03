from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py
from time import sleep

class _RigolIO():
    def __init__(self, resource_str, access_mode):
        assert access_mode in ['eth', 'usb'], 'access_mode must be one of \'eth\' or \'usb\''
        self.access_mode = access_mode

        if self.access_mode == 'eth':
            import socket

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((resource_str, 5555))

            self.rigol = self.socket.makefile('brw')
        elif self.access_mode == 'usb':
            import pyvisa

            self.rigol = pyvisa.ResourceManager().open_resource(resource_str)
            self.socket = None

        return

    def write(self, command):
        command = command + '\n'
        if self.socket is not None:
            command = command.encode('ascii')

        self.rigol.write(command)
        if self.socket is not None:
            self.rigol.flush()
            sleep(20e-3) # Rigol gets sad if commands come too fast. 20ms is empirical limit.

        return

    def query(self, command):
        if self.socket is not None:
            self.write(command)

            resp = self.rigol.readline().decode('ascii').strip()
            self.rigol.readline() # Rigol sends blank line afterwards
            return resp
        else:
            return self.rigol.query(command)

    def close(self):
        self.rigol.close()

        if self.socket is not None:
            self.socket.close()
        return

class _RigolDG4162InterfaceChannel(object):
    def __init__(self, channel, io):
        self.channel = channel
        self.io = io

        self.state = 0
        self.mode = None

        self._clear()

        return

    def _clear(self):
        # Static variables
        self.freq = None
        self.amplitude = None

        # Sweep variables
        self.freq_2 = None
        self.time = None
        self.time_hold_start = None
        self.time_hold_stop = None
        self.time_return = None
        self.spacing = None
        self.steps = None
        self.trigger_slope = None
        self.trigger_source = None
        self.trigger_out = None

        # FM mod variables
        self.mod_amp = None
        self.mod_shape = None

        return

    def get_state(self):
        return self.io.query(':OUTP{}:STAT?'.format(self.channel))

    def get_mode(self):
        return self.mode

    def output_on(self, fresh=False):
        if self.state == 0 or not fresh:
            self.io.write(':OUTP{:d}:STAT ON'.format(self.channel))
        return

    def output_off(self, fresh=False):
        if self.state == 1 or not fresh:
            self.io.write(':OUTP{:d}:STAT OFF'.format(self.channel))
        return

    def get_static_freq(self):
        return self.io.query(':SOUR{}:FREQ?'.format(self.channel))

    def get_static_amplitude(self):
        return self.io.query(':SOUR{}:VOLT?'.format(self.channel))

    def static(self, freq, amplitude, fresh):
        if self.mode != 'static' or not fresh:
            self.io.write(':SOUR{}:SWE:STAT OFF'.format(self.channel))
            self.io.write(':SOUR{}:MOD:STAT OFF'.format(self.channel))
            self.io.write(':OUTP{}:LOAD 50'.format(self.channel))
            self.io.write(':SOUR{}:FUNC:SHAP SIN'.format(self.channel))
            fresh = False

        if self.freq != freq or not fresh:
            self.io.write(':SOUR{}:FREQ {}'.format(self.channel, freq))
        if self.amplitude != amplitude or not fresh:
            self.io.write(':SOUR{}:VOLT:UNIT DBM'.format(self.channel))
            self.io.write(':SOUR{}:VOLT {}'.format(self.channel, amplitude))
            self.io.write(':SOUR{}:VOLT:OFFS 0'.format(self.channel))

        self._clear()
        self.mode = 'static'
        self.freq = freq
        self.amplitude = amplitude

        return

    def get_sweep_freq_start(self):
        return self.io.query(':SOUR{}:FREQ:STAR?'.format(self.channel))

    def get_sweep_freq_stop(self):
        return self.io.query(':SOUR{}:FREQ:STOP?'.format(self.channel))

    def get_sweep_time(self):
        return self.io.query(':SOUR{}:SWE:TIME?'.format(self.channel))

    def get_sweep_time_hold_start(self):
        return self.io.query(':SOUR{}:SWE:HTIM:STAR?'.format(self.channel))

    def get_sweep_time_hold_stop(self):
        return self.io.query(':SOUR{}:SWE:HTIM:STOP?'.format(self.channel))

    def get_sweep_time_return(self):
        return self.io.query(':SOUR{}:SWE:HTIM:RTIM?'.format(self.channel))

    def get_sweep_spacing(self):
        return self.io.query(':SOUR{}:SWE:SPAC?'.format(self.channel))

    def get_sweep_trigger_slope(self):
        return self.io.query(':SOUR{}:SWE:TRIG:SLOP?'.format(self.channel))

    def get_sweep_trigger_source(self):
        return self.io.query(':SOUR{}:SWE:TRIG:SOUR?'.format(self.channel))

    def get_sweep_trigger_out(self):
        return self.io.query(':SOUR{}:SWE:TRIG:TRIGO?'.format(self.channel))

    def get_sweep_steps(self):
        return self.io.query(':SOUR{}:SWE:STEP?'.format(self.channel))

    def sweep(self, freq_start, freq_stop, amplitude,
              time, time_hold_start, time_hold_stop, time_return, spacing,
              trigger_slope, trigger_source, trigger_out, steps, fresh):
        assert spacing in ['LIN', 'LOG', 'STE'], \
            'spacing must be LINear, LOGarithmic, or STEp'
        assert trigger_slope in ['POS', 'NEG'], \
            'trigger_slope must be POSitive or NEGative'
        assert trigger_source in ['EXT', 'INT', 'MAN'], \
            'trigger_source must be EXTernal, INTernal, or MANual'
        assert trigger_out in ['OFF', 'POS', 'NEG'], \
            'trigger_out must be OFF, POSitive or NEGative'

        if time_hold_start == 0:
            time_hold_start = 'MIN'
        if time_hold_stop == 0:
            time_hold_stop = 'MIN'
        if time_return == 0:
            time_return = 'MIN'
        if time == 0:
            time = 'MIN'

        if self.mode != 'sweep' or not fresh:
            self.io.write(':OUTP{}:LOAD 50'.format(self.channel))
            self.io.write(':SOUR{}:FUNC:SHAP SIN'.format(self.channel))
            self.io.write(':SOUR{}:MOD:STAT OFF'.format(self.channel))
            self.io.write(':SOUR{}:SWE:STAT ON'.format(self.channel))
            fresh = False
        if self.freq != freq_start or not fresh:
            self.io.write(':SOUR{}:FREQ:STAR {}'.format(self.channel, freq_start))
        if self.freq_2 != freq_stop or not fresh:
            self.io.write(':SOUR{}:FREQ:STOP {}'.format(self.channel, freq_stop))
        if self.amplitude != amplitude or not fresh:
            self.io.write(':SOUR{}:VOLT:UNIT DBM'.format(self.channel))
            self.io.write(':SOUR{}:VOLT {}'.format(self.channel, amplitude))
            self.io.write(':SOUR{}:VOLT:OFFS 0'.format(self.channel))
        if self.time_hold_start != time_hold_start or not fresh:
            self.io.write(':SOUR{}:SWE:HTIM:STAR {}'.format(self.channel, time_hold_start))
        if self.time_hold_stop != time_hold_stop or not fresh:
            self.io.write(':SOUR{}:SWE:HTIM:STOP {}'.format(self.channel, time_hold_stop))
        if self.time_return != time_return or not fresh:
            self.io.write(':SOUR{}:SWE:HTIM:RTIM {}'.format(self.channel, time_return))
        if self.spacing != spacing or not fresh:
            self.io.write(':SOUR{}:SWE:SPAC '.format(self.channel) + spacing)
        if spacing == 'STE' and (self.steps != steps or not fresh):
            self.io.write(':SOUR{}:SWE:STEP {}'.format(self.channel, steps))
        if self.time != time or not fresh:
            self.io.write(':SOUR{}:SWE:TIME {}'.format(self.channel, time))
        if self.trigger_slope != trigger_slope or not fresh:
            self.io.write(':SOUR{}:SWE:TRIG:SLOP '.format(self.channel) + trigger_slope)
        if self.trigger_source != trigger_source or not fresh:
            self.io.write(':SOUR{}:SWE:TRIG:SOUR '.format(self.channel) + trigger_source)
        if self.trigger_out != trigger_out or not fresh:
            self.io.write(':SOUR{}:SWE:TRIG:TRIGO '.format(self.channel) + trigger_out)

        if trigger_source == 'MAN': # Trigger manual sweep now
            self.io.write(':SOUR{}:SWE:TRIG:IMM'.format(self.channel))

        self._clear()
        self.mode = 'sweep'
        self.freq = freq_start
        self.freq_2 = freq_stop
        self.amplitude = amplitude
        self.time = time
        self.time_hold_start = time_hold_start
        self.time_hold_stop = time_hold_stop
        self.time_return = time_return
        self.spacing = spacing
        self.trigger_slope = trigger_slope
        self.trigger_source = trigger_source
        self.trigger_out = trigger_out
        self.steps = steps

        return

    def get_fm_mod_mod_freq(self):
        return self.io.query(':SOUR{}:MOD:FM:INT:FREQ?'.format(self.channel))

    def get_fm_mod_mod_amp(self):
        return self.io.query(':SOUR{}:MOD:FM:DEV?'.format(self.channel))

    def get_fm_mod_mod_shape(self):
        return self.io.query(':SOUR{}:MOD:FM:INT:FUNC?'.format(self.channel))

    def fm_mod(self, carrier_freq, mod_freq, amplitude, mod_amp, mod_shape, fresh):
        if self.mode != 'fm_mod' or not fresh:
            self.io.write(':OUTP{}:LOAD 50'.format(self.channel))
            self.io.write(':SOUR{}:FUNC:SHAP SIN'.format(self.channel))
            self.io.write(':SOUR{}:SWE:STAT OFF'.format(self.channel))
            self.io.write(':SOUR{}:MOD:STAT ON'.format(self.channel))
            self.io.write(':SOUR{}:MOD:TYP FM'.format(self.channel))
            self.io.write(':SOUR{}:MOD:FM:SOUR INT'.format(self.channel))
            fresh = False
        if self.freq != carrier_freq or not fresh:
            self.io.write(':SOUR{}:FREQ {}'.format(self.channel, carrier_freq))
        if self.amplitude != amplitude or not fresh:
            self.io.write(':SOUR{}:VOLT:UNIT DBM'.format(self.channel))
            self.io.write(':SOUR{}:VOLT {}'.format(self.channel, amplitude))
            self.io.write(':SOUR{}:VOLT:OFFS 0'.format(self.channel))
        if self.freq_2 != mod_freq or not fresh:
            self.io.write(':SOUR{}:MOD:FM:INT:FREQ {}'.format(self.channel, mod_freq))
        if self.mod_amp != mod_amp or not fresh:
            self.io.write(':SOUR{}:MOD:FM:DEV {}'.format(self.channel, mod_amp))
        if self.mod_shape != mod_shape or not fresh:
            self.io.write(':SOUR{}:MOD:FM:INT:FUNC {}'.format(self.channel, mod_shape))

        self._clear()
        self.mode = 'fm_mod'
        self.freq = carrier_freq
        self.freq_2 = mod_freq
        self.amplitude = amplitude
        self.mod_amp = mod_amp
        self.mod_shape = mod_shape

        return

class RigolDG4162Interface(object):
    def __init__(self, resource_str, access_mode):
        self.access_mode = access_mode
        self.io = _RigolIO(resource_str, access_mode)

        self.channels = [_RigolDG4162InterfaceChannel(1, self.io),
                         _RigolDG4162InterfaceChannel(2, self.io)]

        return

    def output_on(self, channel, fresh=False):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].output_on(fresh)

    def output_off(self, channel, fresh=False):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].output_off(fresh)

    def get_state(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_state()

    def get_mode(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_mode()

    def get_static_freq(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_static_freq()

    def get_static_amplitude(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_static_amplitude()

    def static(self, channel, freq=0, amplitude=0, fresh=False):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].static(freq, amplitude, fresh)

    def get_sweep_freq_start(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_freq_start()

    def get_sweep_freq_stop(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_freq_stop()

    def get_sweep_amplitude(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_amplitude()

    def get_sweep_time(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_time()

    def get_sweep_time_hold_start(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_time_hold_start()

    def get_sweep_time_hold_stop(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_time_hold_stop()

    def get_sweep_time_return(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_time_return()

    def get_sweep_spacing(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_spacing()

    def get_sweep_trigger_slope(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_trigger_slope()

    def get_sweep_trigger_source(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_trigger_source()

    def get_sweep_trigger_out(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_trigger_out()

    def get_sweep_steps(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_sweep_steps()

    def sweep(self, channel, freq_start=0, freq_stop=0, amplitude=0,
              time=0, time_hold_start=0, time_hold_stop=0, time_return=0, spacing='LIN',
              trigger_slope='POS', trigger_source='EXT', trigger_out='OFF', steps=0,
              fresh=False):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].sweep(freq_start, freq_stop, amplitude, time,
                                              time_hold_start, time_hold_stop,
                                              time_return, spacing,
                                              trigger_slope, trigger_source,
                                              trigger_out, steps, fresh)

    def get_fm_mod_mod_freq(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_fm_mod_mod_freq()

    def get_fm_mod_mod_amp(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_fm_mod_mod_amp()

    def get_fm_mod_mod_shape(self, channel):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].get_fm_mod_mod_shape()

    def fm_mod(self, channel, carrier_freq, mod_freq, amplitude, mod_amp, mod_shape, fresh=False):
        assert channel in [1, 2], 'channel should be 1 or 2'
        return self.channels[channel-1].fm_mod(carrier_freq, mod_freq, amplitude, mod_amp,
                                               mod_shape, fresh)

    def write(self, command):
        return self.io.write(command)

    def query(self, command):
        return self.io.query(command)

    def close(self):
        return self.io.close()

class Rigol4162Worker(Worker):
    def init(self):
        self.rigol = RigolDG4162Interface(self.resource_str, self.access_mode)

    def check_remote_values(self):
        remove_values = {}
        for channel in [1, 2]:
            state = self.rigol.get_state(channel)
            if state == 'OFF':
                remote_values['channel {:d}'.format(channel)] = {'state': 0}
                continue

            mode = self.rigol.get_mode(channel)

            if mode == 'static':
                cv = {'state': 1, 'mode': 'static',
                      'freq': self.rigol.get_static_freq(channel),
                      'amplitude': self.rigol.get_static_amplitude(channel),}
                remote_values['channel {:d}'.format(channel)] = cv
            elif mode == 'sweep':
                cv = {'state': 1, 'mode': 'sweep',
                      'freq_start': self.rigol.get_sweep_freq_start(channel),
                      'freq_2': self.rigol.get_sweep_freq_stop(channel),
                      'amplitude': self.rigol.get_static_amplitude(channel),
                      'time': self.rigol.get_sweep_time(channel),
                      'time_hold_start': self.rigol.get_sweep_time_hold_start(channel),
                      'time_hold_stop': self.rigol.get_sweep_time_hold_stop(channel),
                      'time_return': self.rigol.get_sweep_time_return(channel),
                      'spacing': self.rigol.get_sweep_spacing(channel),
                      'steps': self.rigol.get_sweep_steps(channel),
                      'trigger_slope': self.rigol.get_sweep_trigger_slope(channel),
                      'trigger_source': self.rigol.get_sweep_trigger_source(channel),
                      'trigger_out': self.rigol.get_sweep_trigger_out(channel)}
                remote_values['channel {:d}'.format(channel)] = cv
            elif mode == 'fm_mod':
                cv = {'state': 1, 'mode': 'fm_mod',
                      'freq': self.rigol.get_static_freq(channel),
                      'freq_2': self.rigol.get_fm_mod_mod_freq(channel),
                      'amplitude': self.rigol.get_static_amplitude(channel),
                      'mod_amp': self.rigol.get_fm_mod_mod_amp(channel),
                      'mod_shape': self.rigol.get_fm_mod_mod_shape(channel)}
                remote_values['channel {:d}'.format(channel)] = cv
            else:
                remote_values['channel {:d}'.format(channel)] = {'state': 0}

        return remote_values

    def program_manual(self, values):
        for channel in [1, 2]:
            key = 'channel {:d}'.format(channel)
            if key in values.keys():
                if values[key] is None:
                    values[key] = {'state': False}
            setting = values[key]

            if not setting['state']:
                self.rigol.output_off(channel)
                continue

            if setting['mode'] == 'static':
                self.rigol.static(channel, setting['freq'], setting['amplitude'])
            elif setting['mode'] == 'sweep':
                self.rigol.sweep(channel, setting['freq'], setting['freq_2'],
                                 setting['amplitude'], setting['time'],
                                 setting['time_hold_start'], setting['time_hold_stop'],
                                 setting['time_return'], setting['spacing'],
                                 setting['trigger_slope'], setting['trigger_source'],
                                 setting['trigger_out'], setting['steps'])
            elif setting['mode'] == 'fm_mod':
                self.rigol.fm_mod(channel, setting['freq'], setting['freq_2'],
                                  setting['amplitude'], setting['mod_amp'], setting['mod_shape'])
            else:
                print('Invalid mode')

            self.rigol.output_on(channel)
        return

    def _parse_channel_dataset(self, dataset):
        state = dataset['state'][0]
        if not state:
            return {'state': 0}

        mode = dataset['mode'][0].decode()
        if mode == 'static':
            return {'state': 1, 'mode': 'static',
                    'freq': dataset['freq'][0], 'amplitude': dataset['amplitude'][0]}
        elif mode == 'sweep':
            return {'state': 1, 'mode': 'sweep',
                    'freq': dataset['freq'][0],
                    'freq_2': dataset['freq_2'][0],
                    'amplitude': dataset['amplitude'][0],
                    'time': dataset['time'][0],
                    'time_hold_start': dataset['time_hold_start'][0],
                    'time_hold_stop': dataset['time_hold_stop'][0],
                    'time_return': dataset['time_return'][0],
                    'spacing': dataset['spacing'][0].decode(),
                    'steps': dataset['steps'][0],
                    'trigger_slope': dataset['trigger_slope'][0].decode(),
                    'trigger_source': dataset['trigger_source'][0].decode(),
                    'trigger_out': dataset['trigger_out'][0].decode()}
        elif mode == 'fm_mod':
            return {'state': 1, 'mode': 'fm_mod',
                    'freq': dataset['freq'][0],
                    'freq_2': dataset['freq_2'][0],
                    'amplitude': dataset['amplitude'][0],
                    'mod_amp': dataset['mod_amp'][0],
                    'mod_shape': dataset['mod_shape'][0]}
        else:
            return {'state': 0}

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['/devices/' + device_name]
            values = {}
            if 'channel 1' in group:
                values['channel 1'] = self._parse_channel_dataset(group['channel 1'])
            else:
                values['channel 1'] = {'state': False}
            if 'channel 2' in group:
                values['channel 2'] = self._parse_channel_dataset(group['channel 2'])
            else:
                values['channel 2'] = {'state': False}
        self.program_manual(values)
        return {}

    def transition_to_manual(self):
        return True

    def abort_buffered(self):
        return True

    def abort_transition_to_buffered(self):
        return True

    def shutdown(self):
        self.rigol.close()
