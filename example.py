#!/usr/bin/python3
import logging
from time import sleep
from ypmeteo import ypmeteo

logging.basicConfig(level=logging.DEBUG)

with ypmeteo() as m:
    while True:
        if m.connected():
            print('{0:0.1f} °C, {1:0.0f} %rh, {2:0.1f} hPa'.format(
                m.t, m.h, m.p))
        else:
            print('Yocto-Meteo not connected')
        sleep(5.0)
