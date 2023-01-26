# bbswitch-gui

GUI for monitoring and toggling NVIDIA GPU power on Optimus laptops.

Provides a user-friendly interface for managing power state
and monitoring utilization of dedicated graphics adapter.

![ Preview ](data/screenshots/preview.png)

Useful for pre-Turing GPU generations without dynamic power management features,
allows to fully benefit from NVIDIA
[PRIME Render Offload](https://download.nvidia.com/XFree86/Linux-x86_64/495.46/README/primerenderoffload.html)
technology without need to keep graphics adapter turned on all the time.

For Turing generation cards with Intel Coffee Lake or above CPUs as well as some
Ryzen CPUs like the 5800H, it is possible to fully power down the GPU when not in use
automatically without user interaction:
[see NVIDIA documentation](https://us.download.nvidia.com/XFree86/Linux-x86_64/495.46/README/dynamicpowermanagement.html).

Uses [bbswitchd](https://github.com/polter-rnd/bbswitchd) daemon
to switch video adapter power state (`ON` or `OFF`) and NVML to monitor GPU parameters.

## Installation

#### Requirements

Check if you have `PyGObject` module installed (usually available in you Linux ditribution),
`pynvml` module for gathering GPU information, `fuser` utility to find processes using video card
and `GTK+` library for GUI (development package is not needed).

For Fedora:

```bash
$ sudo dnf install gtk3 python3-gobject python3-py3nvml psmisc
```

For Ubuntu:

```bash
$ sudo apt-get install libgtk-3-0 python3-gi python3-pynvml psmisc
```

To be able to manage dedicated GPU power state, you also need to install `bbswitchd` daemon.
Refer to *Installation* section [here](https://github.com/polter-rnd/bbswitchd).

#### Installing using pip

You can build and install a `wheel` or `egg` package using `pip`.

Example of per-user installation:

```bash
$ python3 -m pip install --user .
```

And system-wide:

```bash
$ python3 -m pip install .
```

After that `bbswitch-gui` command will appear in your `PATH`.
Desktop files are not created when installing by `pip`.


#### Installing using meson

First you need to install `meson` build system:

For Fedora:

```bash
$ sudo dnf install meson
```

For Ubuntu:

```bash
$ sudo apt-get install meson
```

Then build and install the project (specify `--prefix` argument
if you need to unstall somewhere not in `/usr/local`):

```bash
$ meson build # --prefix=/usr
```

To install the package on your system:

```bash
$ sudo meson install -C build
```

After that `bbswitch-gui` command will appear in your `PATH`
and `bbswitch-gui.desktop` will appear in menu.

## Usage

Run `bbswitch-gui` command or select `BBswitch GUI` app from menu, the window will appear:

![ Main window with GPU disabled ](data/screenshots/gpu_disabled.png)

You can turn dedicated graphics card on and off using switch control in the top left corner,
after that GPU monitoring panel will appear:

![ Main window with GPU enabled ](data/screenshots/gpu_enabled.png)

If you have [switchroo-control](https://gitlab.freedesktop.org/hadess/switcheroo-control)
installed, after GPU has been enabled you should be able to launch any application
on dedicated graphics card by right-click in GNOME shell:

![ Launch using Discrete Graphics Card ](data/screenshots/launch_discrete.png)

To launch from console you need to setup environment variables, e.g.:

```bash
$ __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxgears
```

To use PRIME offload for Vulkan applications:

```
$ __NV_PRIME_RENDER_OFFLOAD=1 __VK_LAYER_NV_optimus=NVIDIA_only vkmark
```

Then you will see a list of applications using the dedicated GPU:

![ Main window with process list ](data/screenshots/process_list.png)

You won't be able to turn GPU off while some application still uses it.
To force killing them you can check desired processes and click **Kill selected processes**
button.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

This software is distributed under [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html).
See `LICENSE` file for more information.