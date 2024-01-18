"""Module containing tray indicator."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import GObject, Gtk, AppIndicator3  # pyright: ignore

from .nvidia import NVidiaGpuStats


class Indicator(GObject.GObject):
    """Tray Indicator."""

    __gtype_name__ = "Indicator"
    __gsignals__ = {
        'open-requested': (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE, ()),
        'exit-requested': (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE, ()),
    }

    def __init__(self, **kwargs) -> None:
        """Initialize Tray Indicator."""
        super().__init__(**kwargs)

        self._app_indicator = AppIndicator3.Indicator.new(
            'customtray', 'bbswitch-tray-symbolic',
            AppIndicator3.IndicatorCategory.HARDWARE)
        self._app_indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._gpu_name = "N/A"
        self._gpu_stats = None

    def reset(self) -> None:
        """Reset indicator to default state."""
        self._app_indicator.set_menu(self._menu())

    def set_gpu_name(self, gpu_name: str) -> None:
        """Set the GPU name in the applet mouseover text."""
        self._gpu_name = gpu_name
        self._update_title()

    def set_gpu_stats(self, gpu_stats: NVidiaGpuStats) -> None:
        """Set the GPU statistics in the applet mouseover text."""
        self._gpu_stats = gpu_stats
        self._update_title()

    def _update_title(self):
        if self._gpu_stats is None:
            self._app_indicator.set_title(self._gpu_name)            
        else:
            title = "{} ({}%, {:.2f}W, {}MHz)".format(
                self._gpu_name, 
                self._gpu_stats['gpu_util'], 
                self._gpu_stats['power_draw'],
                self._gpu_stats['gpu_freq'],
            )
            self._app_indicator.set_title(title)

    def _menu(self):
        menu = Gtk.Menu()

        open_item = Gtk.MenuItem('Open')
        open_item.connect('activate', self._request_open)
        menu.append(open_item)

        close_item = Gtk.MenuItem('Exit')
        close_item.connect('activate', self._request_exit)
        menu.append(close_item)

        menu.show_all()
        return menu

    def _request_open(self, menuitem):
        del menuitem  # unused argument
        self.emit('open-requested')

    def _request_exit(self, menuitem):
        del menuitem  # unused argument
        self.emit('exit-requested')
