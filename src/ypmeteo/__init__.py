"""Python/libusb Yocto-Meteo Interface."""

import logging
import usb.core
from threading import Thread
from time import sleep

# USB product and vendor
IDVENDOR = 0x24e0
IDPRODUCT = 0x0018

# Meteo 'start' command
SCMD = bytearray(64)
SCMD[1] = 0xf9
SCMD[2] = 0x09
SCMD[3] = 0x02
SCMD[4] = 0x01

# Meteo 'config' command
CCMD = bytearray(64)
CCMD[0] = 0x08
CCMD[1] = 0xf9
CCMD[2] = 0x01

_log = logging.getLogger(__name__)


class ypmeteo(Thread):
    """Yocto-Meteo Thread Object"""

    def __init__(self, timeout=0):
        """Create ypmeteo thread object."""
        Thread.__init__(self)
        self.daemon = True
        self.__m = None
        self.__ct = None
        if timeout is not None:
            self.__ct = float(timeout)
        self.__stat = False
        self.__running = None
        self.t = 0.0
        self.h = 0.0
        self.p = 0.0

    def connected(self):
        """Return the connection status flag."""
        return self.__stat

    def exit(self):
        """Request thread termination."""
        _log.debug('request to exit')
        self.__running = False

    def __connect(self):
        """Request re-connect, exceptions should bubble up to run loop."""
        self.__cleanup()
        self.__stat = False
        self.__m = usb.core.find(idVendor=IDVENDOR, idProduct=IDPRODUCT)
        _log.debug('USB find device: %r', self.__m)
        if self.__m is not None:
            if self.__m.is_kernel_driver_active(0):
                _log.debug('detach kernel driver')
                self.__m.detach_kernel_driver(0)
            self.__m.reset()
            # clear any junk in the read buffer - so that init cmds will send
            try:
                while True:
                    _log.debug('read stale junk from command buffer')
                    junk = self.__m.read(0x81, 64, 50)
            except usb.core.USBError as e:
                # Ignore timeout
                if e.errno == 110:
                    pass
                else:
                    raise
            # send start and conf commands, errors are collected in run
            self.__m.write(0x01, SCMD)
            self.__m.write(0x01, CCMD)
            self.__stat = True

    def __cleanup(self):
        """Close current usb connection and clean up used resources."""
        if self.__m is not None:
            try:
                _log.debug('dispose usb resources')
                usb.util.dispose_resources(self.__m)
            except:
                _log.warning('error disposing usb connection resources')
                pass
        self.__m = None
        self.__stat = False
        sleep(0.01)  # release thread

    def __read(self):
        bd = bytearray(self.__m.read(0x81, 64))
        #_log.debug('RCV: %r', bd)
        of = 0
        while of < 64:
            pktno = bd[of] & 0x7
            stream = (bd[of] >> 3) & 0x1f
            pkt = bd[of + 1] & 0x3
            size = (bd[of + 1] >> 2) & 0x3f
            if stream == 3 and size > 0:
                sb = bd[of + 2]
                if sb in [0x01, 0x02, 0x03]:
                    val = float(bd[of + 3:of + 3 + size - 1].decode(
                        'ascii', 'ignore'))
                    #_log.debug('pktno:%r, stream:%r, size:%r, sb:%r, val:%r',
                               #pktno, stream, size, sb, val)
                    if sb == 1:
                        _log.debug('Temperature: %r', val)
                        self.t = val
                    elif sb == 2:
                        _log.debug('Pressure: %r', val)
                        self.p = val
                    elif sb == 3:
                        _log.debug('Humidity: %r', val)
                        self.h = val
            of += size + 2

    def run(self):
        """Called via Thread.start()."""
        _log.debug('Starting')
        if self.__running is None:
            # exit may set this to False before run is called
            self.__running = True
        while self.__running:
            try:
                if self.__stat and self.__m is not None:
                    try:
                        self.__read()
                    except usb.core.USBError as e:
                        # Ignore timeout
                        if e.errno == 110:
                            pass
                        else:
                            raise
                else:
                    self.__connect()
                    _log.debug('re-connect: %r', self.__m)
                    if self.__m is None:
                        sleep(5.0)
            except Exception as e:
                _log.error('%s: %s', e.__class__.__name__, e)
                self.__stat = False
                sleep(1.0)
        self.__cleanup()
        _log.debug('exiting')

    def __enter__(self):
        _log.debug('enter context')
        self.start()
        while not self.__stat:
            if self.__ct is not None:
                self.__ct -= 0.1
                if not self.__ct > 0.01:
                    break
            sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _log.debug('exit context exc_type=%r', exc_type)
        self.exit()
        if exc_type is not None:
            return False  # raise exception
        self.join()
        return True
