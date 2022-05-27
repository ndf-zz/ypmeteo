# ypmeteo

ypmeteo is a python library for extracting environmental data
directly from a Yoctopuce
[Yocto-Meteo](https://www.yoctopuce.com/EN/products/usb-sensors/yocto-meteo)
USB weather module using plain python and libusb.


## Installation

	$ pip install ypmeteo


## Usage

	with ypmeteo.connect() as m:
	    print('{0:0.1f} °C'.format(m.t))
	    print('{0:0.0f} %rh'.format(m.h))
	    print('{0:0.1f} hPa'.format(m.p))


## Limitations

This library will only read from the first detected Yocto-Meteo module
with USB id 24e0:0018. If additional units are required, Yoctopuce
[API](https://www.yoctopuce.com/EN/libraries.php)
or virtual hub may be a better fit.

Meteo-V2 is not supported.


## Requirements

   - pyusb
   - libusb-1.0-0


## Links

   - Product page: [Yoctopuce Meteo](https://www.yoctopuce.com/EN/products/usb-sensors/yocto-meteo)
   - Yocto API: [Libraries](https://www.yoctopuce.com/EN/products/usb-sensors/yocto-meteo)
