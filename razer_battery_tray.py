import os
import sys
from functools import lru_cache
from time import sleep

import openrazer.client
import PIL.Image
from pystray import Icon, Menu, MenuItem

RESIZE_TO_PIXELS = 32
SCALE = (RESIZE_TO_PIXELS, RESIZE_TO_PIXELS)
UPDATE_INTERVAL_IN_SECS = 1 / 5

print("Starting Razer Battery Tray")

real_path = os.path.realpath(__file__)  # Finding target of Symlink
script_path = os.path.dirname(real_path)
icons_path = os.path.join(script_path, "icons")

if hasattr(PIL.Image, "Resampling"):  # Pillow >= 9.1.0
    DOWNSCALE_METHOD = PIL.Image.Resampling.LANCZOS
else:  # Pillow < 9.1.0
    DOWNSCALE_METHOD = PIL.Image.LANCZOS

try:
    print("Pillow version: ", PIL.__version__)
    print("Openrazer version: ", openrazer.client.__version__)
    print("Python version: ", sys.version)
    print("Path of the icons:", icons_path)

    try:
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8 or higher is required")
        from importlib.metadata import version

        print("Pystray version: ", version("pystray"))
    except:
        print("Cannot get pystray version (Python 3.8+ is required for that..):")
except:
    print("Failed to get all version infos, please check your installation")


a = openrazer.client.DeviceManager()
device = None
print(a.devices)
if len(sys.argv) < 2:
    for dev in a.devices:  # print all bat devices
        print(dev.name, "\n    Has Battery:", dev.has("battery"))
        device = dev
else:
    device_name_param = sys.argv[1].lower()

    for dev in a.devices:  # find the device we want to monitor
        if device_name_param in dev.name.lower():
            device = dev
            print("Found device:", dev.name)
            break

if device is None:
    print("Device not found, check the name and try again.")
    sys.exit(1)


def refresh():
    print("refreshing")
    a = openrazer.client.DeviceManager()
    global device
    for dev in a.devices:  # print all bat devices
        print(dev.name, "\n    Has Battery:", dev.has("battery"))
        device = dev
    on_monitor(tray_icon)


@lru_cache(maxsize=256)
def get_icon(bat_level, charging=False):
    """
    Get the icon for the given battery level
    """
    name = f"bat_{bat_level}.png" if not charging else f"bat_{bat_level}_c.png"
    icon_path = os.path.join(icons_path, name)
    icon = PIL.Image.open(icon_path).resize(SCALE, DOWNSCALE_METHOD)
    return icon


def setup_icon(icon):
    icon.visible = True
    sleep(1)  # wait for the icon to be visible
    bat_level = device.battery_level
    is_charging = device.is_charging

    print("Animating icon to current battery level")
    for i in range(100, 0, -4):
        icon.icon = get_icon(i)
        sleep(1 / 30)
    for i in range(0, bat_level + 1, 2):
        icon.icon = get_icon(i)
        sleep(1 / 30)
    print(f"Icon set to {bat_level}% {'(charging)' if is_charging else ''}")

    # start the update loop
    while True:
        try:
            bat_level = device.battery_level
            is_charging = device.is_charging
            cur_icon = get_icon(bat_level, is_charging)
            if cur_icon != icon.icon:
                icon.icon = cur_icon
                print(f"Icon set to {bat_level}% {'(charging)' if is_charging else ''}")
            sleep(UPDATE_INTERVAL_IN_SECS)
        except KeyboardInterrupt:
            print("Exiting")
            break
        except Exception as e:
            print("Error:", e)
            sleep(UPDATE_INTERVAL_IN_SECS)
            refresh()


def on_monitor(icon):
    global device, device_name
    device_name = device.name


device_name = device.name
tray_icon = Icon(
    "BatteryIcon",
    get_icon(100),
    menu=Menu(
        MenuItem(
            lambda text: device_name,
            on_monitor,
        ),
        MenuItem(f"Refresh", lambda: refresh()),
        MenuItem(
            f"Exit",
            lambda: os._exit(0),
        ),
    ),
)

tray_icon.run(setup=setup_icon)
