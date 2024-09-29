from labscript import AnalogQuantity

import numpy as np

class AnalogRamper(AnalogQuantity):
    """Analog Output class for use with devices that perform linear ramps at the device level.
    """

    def expand_timeseries(self, all_times, flat_all_times_len):
        """This function evaluates the ramp functions in self.timeseries
        at the time points in all_times, and creates an array of constants
        or linear ramps at those times.  These are the ramps that this output
        should start on each clock tick, and are the raw values that
        should be used to program the output device.  They are stored
        in self.raw_output in the format
        ((float) duration, (se.fldtype) start value,
        (self.dtype) end value, (bool) wait for trigger)."""
        self.raw_output = np.empty(flat_all_times_len,
                                   dtype=[('duration', float),
                                          ('start_value', np.dtype(self.dtype)),
                                          ('end_value', np.dtype(self.dtype))])
        # If this output is not ramping, then its timeseries should
        # not be expanded. It's already as expanded as it'll get.
        # This is overly restrictive for ramps that occur at device level,
        # but for now we will ignore that.
        if not self.parent_clock_line.ramping_allowed:
            self.raw_output['duration'] = np.zeros(flat_all_times_len)
            self.raw_output['start_value'] = self.timeseries
            self.raw_output['end_value'] = self.timeseries
            return
        j = 0
        for i in range(len(all_times) - 1):
            if np.iterable(all_times[i]):
                time_len = len(all_times[i])
                if isinstance(self.timeseries[i], dict):
                    next_time = all_times[i+1][0] if np.iterable(all_times[i+1]) else all_times[i+1]
                    times = np.concatenate([all_times[i], [next_time]])

                    start_values = self.timeseries[i]['function'](
                        times[:-1] - self.timeseries[i]['initial time']
                    )
                    end_values = self.timeseries[i]['function'](
                        times[1:] - self.timeseries[i]['initial time']
                    )
                    durations = times[1:] - times[:-1]

                    # Calibrate
                    if self.timeseries[i]['units'] is not None:
                        start_values = self.apply_calibration(
                            start_values, self.timeseries[i]['units']
                        )
                        end_values = self.apply_calibration(
                            end_values, self.timeseries[i]['units']
                        )

                    # Check limits
                    if self.limits:
                        if ((start_values < self.limits[0]) | (start_values > self.limits[1])).any():
                            raise LabscriptError(
                                f"The function {self.timeseries[i]['function']} called "
                                f'on "{self.name}" at t={times[0]} generated a '
                                "value which falls outside the base unit limits "
                                f"({self.limits[0]} to {self.limits[1]})"
                            )
                        if ((end_values < self.limits[0]) | (end_values > self.limits[1])).any():
                            raise LabscriptError(
                                f"The function {self.timeseries[i]['function']} called "
                                f'on "{self.name}" at t={times[0]} generated a '
                                "value which falls outside the base unit limits "
                                f"({self.limits[0]} to {self.limits[1]})"
                            )
                else:
                    start_values = np.empty(time_len, dtype=self.dtype)
                    start_values.fill(self.timeseries[i])
                    end_values = np.empty(time_len, dtype=self.dtype)
                    end_values.fill(self.timeseries[i])
                    durations = np.empty(time_len, dtype=self.dtype)
                    end_values.fill(0.0)

                self.raw_output['duration'][j:j+time_len] = durations
                self.raw_output['start_value'][j:j+time_len] = start_values
                self.raw_output['end_value'][j:j+time_len] = end_values
                j += time_len
            else:
                self.raw_output['duration'][j] = all_times[i+1] - all_times[i]
                self.raw_output['start_value'][j] = self.timeseries[i]
                self.raw_output['end_value'][j] = self.timeseries[i]

        del self.timeseries # don't need this any more.
