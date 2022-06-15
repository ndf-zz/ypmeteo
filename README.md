# ypmeteo

ypmeteo is a python library for extracting temperature, humidity
and pressure data directly from a Yoctopuce
[Yocto-Meteo](https://www.yoctopuce.com/EN/products/usb-sensors/yocto-meteo)
USB weather module using libusb.


## Installation

	$ pip install ypmeteo

ypmeteo requires read/write access to a USB device file,
see (60-ypmeteo.rules) for an example udev rule to
place an attached Yocto-Meteo device in group plugdev.

## Usage

	with ypmeteo.connect() as m:
	    print('{0:0.1f} °C'.format(m.t))
	    print('{0:0.0f} %rh'.format(m.h))
	    print('{0:0.1f} hPa'.format(m.p))


## Limitations

This library will only read from the first detected Yocto-Meteo module
(USB id 24e0:0018). If support for additional units is required,
Yoctopuce [API](https://www.yoctopuce.com/EN/libraries.php)
or virtual hub may be a better fit.

Meteo-V2 is untested.


## Requirements

   - pyusb (libusb)


## Links

   - Product page: [Yoctopuce Meteo](https://www.yoctopuce.com/EN/products/usb-sensors/yocto-meteo)
   - Yocto API: [Libraries](https://www.yoctopuce.com/EN/products/usb-sensors/yocto-meteo)
