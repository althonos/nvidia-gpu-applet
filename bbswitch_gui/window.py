"""Module containing the user interface."""

import os
import signal
import logging

from typing import cast
from pkg_resources import resource_filename

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import GObject, Gtk, Gdk  # pyright: ignore

from .nvidia import NVidiaGpuInfo

logger = logging.getLogger(__name__)


@Gtk.Template(filename=resource_filename(__name__, 'ui/bbswitch-gui.glade'))
class MainWindow(Gtk.ApplicationWindow):
    """Main application window."""

    __gtype_name__ = "MainWindow"
    __gsignals__ = {
        'power-state-switch-requested': (GObject.SIGNAL_RUN_LAST,
                                         GObject.TYPE_NONE, (bool,))
    }

    modules_label = cast(Gtk.Label, Gtk.Template.Child())

    monitor_bar = cast(Gtk.InfoBar, Gtk.Template.Child())
    temperature_label = cast(Gtk.Label, Gtk.Template.Child())
    power_label = cast(Gtk.Label, Gtk.Template.Child())
    memory_label = cast(Gtk.Label, Gtk.Template.Child())
    utilization_label = cast(Gtk.Label, Gtk.Template.Child())

    bar_stack = cast(Gtk.Stack, Gtk.Template.Child())
    info_label = cast(Gtk.Label, Gtk.Template.Child())
    error_label = cast(Gtk.Label, Gtk.Template.Child())
    warning_label = cast(Gtk.Label, Gtk.Template.Child())
    header_bar = cast(Gtk.HeaderBar, Gtk.Template.Child())

    processes_store = cast(Gtk.ListStore, Gtk.Template.Child())
    processes_view = cast(Gtk.TreeView, Gtk.Template.Child())
    pid_column = cast(Gtk.TreeViewColumn, Gtk.Template.Child())
    memory_column = cast(Gtk.TreeViewColumn, Gtk.Template.Child())
    name_column = cast(Gtk.TreeViewColumn, Gtk.Template.Child())
    check_column = cast(Gtk.TreeViewColumn, Gtk.Template.Child())

    kill_button = cast(Gtk.Button, Gtk.Template.Child())
    toggle_button = cast(Gtk.Button, Gtk.Template.Child())

    def __init__(self, app, **kwargs) -> None:
        """Initialize GUI widgets."""
        super().__init__(**kwargs)
        self.set_application(app)

        provider = Gtk.CssProvider()
        provider.load_from_path(resource_filename(
            __name__, 'ui/style.css'))  # type: ignore

        screen = Gdk.Screen.get_default()
        if screen:
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        number_renderer = Gtk.CellRendererText()
        number_renderer.set_property('xalign', 1.0)
        self.pid_column.pack_start(number_renderer, True)
        self.pid_column.add_attribute(number_renderer, 'text', 0)
        self.memory_column.pack_start(number_renderer, True)
        self.memory_column.add_attribute(number_renderer, 'text', 1)

        text_renderer = Gtk.CellRendererText()
        self.name_column.pack_start(text_renderer, True)
        self.name_column.add_attribute(text_renderer, 'text', 2)

        check_renderer = Gtk.CellRendererToggle()
        self.check_column.pack_start(check_renderer, False)
        self.check_column.add_attribute(check_renderer, 'active', 3)

    def reset(self) -> None:
        """Reset window to default state."""
        self.kill_button.set_sensitive(False)
        self.toggle_button.set_sensitive(False)
        self.processes_store.clear()
        self.bar_stack.hide()

    def update_header(self, bus_id: str, enabled: bool, vendor: str, device: str) -> None:
        """Update headerbar for selected GPU.

        :param bus_id: PCI bus ID
        :param enabled: is GPU enabled (`True` or `False`)
        :param vendor: PCI vendor name (or `None` if not available)
        :param device: PCI device name (or `None` if not available)
        """
        if device is None:
            self.header_bar.set_title(f'NVIDIA GPU on {bus_id}')
        else:
            self.header_bar.set_title(
                device[device.find('[') + 1:device.find(']')])  # type: ignore

        if vendor is not None:
            self.header_bar.set_subtitle(vendor)

    def update_monitor(self, gpu_info: NVidiaGpuInfo) -> None:
        """Update UI for selected GPU.

        :param gpu_info: Dictionary of additional GPU information
        """
        self._set_bar_stack_page('monitor')

        # Helper to convert memory in megabytes to string
        def format_mem(used: int, total: int = None) -> str:
            if used == -1:
                return 'N/A'
            if total is None:
                total = used
                limit = False
            else:
                limit = True
            units = iter(['B', 'kiB', 'MiB', 'GiB', 'TiB'])
            unit = next(units)
            while total > 1024:
                used /= 1024
                total /= 1024
                unit = next(units)
            if unit == "B":
                format_ = ""
            else:
                format_ = ".1f"
            return f'{used:{format_}} / {total:{format_}} {unit}' if limit else f'{used:{format_}} {unit}'

        # Update GPU parameters
        self.temperature_label.set_text(str(gpu_info['gpu_temp']) + ' °C')
        self.power_label.set_text(f"{gpu_info['power_draw']:.2f} / {gpu_info['power_limit']:.0f} W")
        self.memory_label.set_text(format_mem(gpu_info['mem_used'], gpu_info['mem_total']))
        self.utilization_label.set_text(str(gpu_info['gpu_util']) + ' %')

        # Update existing PIDs
        processes = gpu_info['processes'].copy()
        i = self.processes_store.get_iter_first()
        while i is not None:
            i_next = self.processes_store.iter_next(i)
            pid = self.processes_store.get_value(i, 0)
            cmdline = self.processes_store.get_value(i, 2)
            process = next((p for p in processes if p['pid'] == pid), None)
            if process is not None and process['cmdline'] == cmdline:
                self.processes_store.set_value(i, 1, format_mem(process['mem_used']))
                processes.remove(process)
            else:
                self.processes_store.remove(i)
            i = i_next

        # Add new PIDs
        for process in processes:
            self.processes_store.append([
                process['pid'],
                format_mem(process['mem_used']),
                process['cmdline'],
                False
            ])

        # Update modules
        self.modules_label.set_text(
            '\n'.join(['• ' + m for m in gpu_info['modules']]))

    def show_info(self, message) -> None:
        """Show information bar with informational message.

        :param message: Error text
        """
        self.info_label.set_text(message)
        self._set_bar_stack_page('info')

    def show_warning(self, message) -> None:
        """Show information bar with warning message.

        :param message: Error text
        """
        self.warning_label.set_text(message)
        self._set_bar_stack_page('warning')

    def show_error(self, message) -> None:
        """Show information bar with error message.

        :param message: Error text
        """
        self.error_label.set_text(message)
        self._set_bar_stack_page('error')

    def error_dialog(self, title, message) -> None:
        """Raise modal message dialog with error text.

        :param message: Error text
        """
        dialog = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def set_cursor_busy(self) -> None:
        """Set the mouse to be a hourglass."""
        gdk_window = self.get_window()
        if gdk_window:
            watch = Gdk.Cursor(Gdk.CursorType.WATCH)
            gdk_window.set_cursor(watch)

    def set_cursor_arrow(self):
        """Set the mouse to be a normal arrow."""
        gdk_window = self.get_window()
        if gdk_window:
            arrow = Gdk.Cursor(Gdk.CursorType.ARROW)
            gdk_window.set_cursor(arrow)

    def _set_bar_stack_page(self, name: str):
        page = self.bar_stack.get_child_by_name(name)
        if page:
            self.bar_stack.show()
            self.bar_stack.set_visible_child(page)

    def _get_selected_pids(self):
        pids = []
        self.processes_store.foreach(
            lambda store, path, iter, data:
                data.append(store[path][0]) if store[path][3] else None,
            pids)
        return pids

    @Gtk.Template.Callback()
    def _on_process_activated(self, treeview, path, column):
        del treeview, column  # unused argument
        # pylint: disable=unsubscriptable-object
        self.processes_store[path][3] = not self.processes_store[path][3]
        self.kill_button.set_sensitive(len(self._get_selected_pids()) > 0)

    @Gtk.Template.Callback()
    def _on_process_added_or_removed(self, store, path=None, iterator=None):
        del store, path, iterator  # unused argument
        self.kill_button.set_sensitive(len(self._get_selected_pids()) > 0)
        self.toggle_button.set_sensitive(self.processes_store.iter_n_children(None) > 0)

    @Gtk.Template.Callback()
    def _on_kill_button_clicked(self, button):
        del button  # unused argument
        for pid in self._get_selected_pids():
            os.kill(pid, signal.SIGKILL)

    @Gtk.Template.Callback()
    def _on_toggle_button_clicked(self, button):
        del button  # unused argument
        row_count = self.processes_store.iter_n_children(None)
        if row_count == 0:
            # Nothing to select/deselect
            return
        if row_count != len(self._get_selected_pids()):
            # Select all
            self.processes_store.foreach(
                lambda store, path, iter: store.set_value(iter, 3, True))
            self.kill_button.set_sensitive(True)
        else:
            # Deselect all
            self.processes_store.foreach(
                lambda store, path, iter: store.set_value(iter, 3, False))
            self.kill_button.set_sensitive(False)
