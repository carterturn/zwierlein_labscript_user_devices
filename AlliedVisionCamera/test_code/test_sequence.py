from labscript import start, stop, add_time_marker

from labscript_utils import import_or_reload
import_or_reload('labscriptlib')
import_or_reload('labscriptlib.fermi2')
connection_table = import_or_reload('labscriptlib.fermi2.connection_table')

if __name__ == '__main__':
    connection_table.load()

    start()
    t = 0

    out_0.enable(t)
    t += 1 
    out_0.disable(t)
    t += 1 
    out_0.enable(t)
    t += 1e-5
    t += camera_0.expose(t, 'e0', 'b0')
    out_0.disable(t)
    t += 0.5
    t += camera_0.expose(t, 'e0', 'd0')
    t += 5e-3

    stop(t=t)
