from labscript import start, stop, add_time_marker

from labscript_utils import import_or_reload
import_or_reload('labscriptlib')
import_or_reload('labscriptlib.fermi2')
connection_table = import_or_reload('labscriptlib.fermi2.connection_table')

if __name__ == '__main__':
    connection_table.load()

    start()
    t = 0

    t += 0.5

    t_light = t
    t_trigger = t_light - 0.03
    out_0.enable(t_light)
    out_0.disable(t_light + 5e-3)
    camera_0.expose(t_trigger, 'e0', 'b0')
    t += 0.5
    camera_0.expose(t, 'e0', 'd0')
    t += 0.5

    stop(t=t)
