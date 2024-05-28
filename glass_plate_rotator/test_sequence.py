'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript import start, stop

from labscript_utils import import_or_reload
import_or_reload('labscriptlib')
import_or_reload('labscriptlib.fermi2')
connection_table = import_or_reload('labscriptlib.fermi2.connection_table')

if __name__ == '__main__':
    connection_table.load()

    start()

    raman_gp.set_upper('Raman X', 37)
    raman_gp.set_upper('Raman Y', 27)
    raman_gp.set_lower('Raman X', 27)
    raman_gp.set_lower('Raman Y', 25)

    stop(1)
