from gi.repository import Gtk, GLib
import os, signal

class MySpawned(Gtk.Window):
    def __init__(self , p):
        self.params = p

        Gtk.Window.__init__(self)
        self.set_default_size(400,300)

        vb = Gtk.VBox(False, 5)

        self.tw_out = Gtk.TextView()

        sw = Gtk.ScrolledWindow()
        vb.pack_start(sw, True, True, 0)
        sw.add(self.tw_out)

        self.progress = Gtk.ProgressBar()
        vb.pack_start(self.progress, False, True, 0)



        self.bt = Gtk.Button('Stop')
        self.bt.connect('clicked', self.kill)
        vb.pack_start(self.bt, False, False, 0)

        self.add(vb)
        self.set_size_request(200, 300)

        self.show_all()
        self.finished = False
        self.process()

    def run(self):
        self.show()


    def update_progress(self, data=None):
        self.progress.pulse()
        return True

    def kill(self, widget, data=None):
        if not self.finished:
            os.kill(self.pid, signal.SIGTERM)
        else:
            self.hide()

    def process(self, *widget, data=None):
        params = self.params #['adb' , '-s' ,'BX902ZYDNS' , 'install' , '/home/alireza/Downloads/com.lockscreen.sony.apk' ]# # ['du', '--si', '/']

        def scroll_to_end(textview):
            i = textview.props.buffer.get_end_iter()
            mark = textview.props.buffer.get_insert()
            textview.props.buffer.place_cursor(i)
            textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

        def write_to_textview(io, condition, tw):
            if condition is GLib.IO_HUP:
                GLib.source_remove(self.source_id_out)
                GLib.source_remove(self.source_id_err)
                return False

            line = io.readline()
            tw.props.buffer.insert_at_cursor(line)
            scroll_to_end(tw)

            while Gtk.events_pending():
                Gtk.main_iteration_do(False)

            return True

        self.pid, stdin, stdout, stderr = GLib.spawn_async(params,
            flags=GLib.SpawnFlags.SEARCH_PATH|GLib.SpawnFlags.DO_NOT_REAP_CHILD,                                       
            standard_output=True,
            standard_error=True)


        io = GLib.IOChannel(stdout)
        err = GLib.IOChannel(stderr)

        self.source_id_out = io.add_watch(GLib.IO_IN|GLib.IO_HUP,
                                 write_to_textview,
                                 self.tw_out,
                                 priority=GLib.PRIORITY_HIGH)

        self.source_id_err = err.add_watch(GLib.IO_IN|GLib.IO_HUP,
                                 write_to_textview,
                                 self.tw_err,
                                 priority=GLib.PRIORITY_HIGH)

        timeout_id = GLib.timeout_add(100, self.update_progress)

        def closure_func(pid, status, data):
            GLib.spawn_close_pid(pid)
            GLib.source_remove(timeout_id)
            self.progress.set_fraction(0.0)
            self.bt.set_label('Close')
            self.finished = True

        GLib.child_watch_add(self.pid, closure_func, None)
