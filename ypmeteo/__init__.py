"""Python/libusb Yocto-Meteo Interface."""

import threading
import logging
import time
import usb.core

# USB Product and Vendor values
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


class ypmeteo(threading.Thread):
    """Yocto-Meteo Thread Object"""

    def __init__(self, timeout=None):
        _log.debug('ypmeteo init')
        threading.Thread.__init__(self)
        _log.debug('thread init')
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
        _log.debug('Connected=%r', self.__stat)
        return self.__stat

    def envstr(self):
        """Return a formatted environment string."""
        ret = u'n/a'
        if self.connected():
            ret = u'{0:0.1f},{1:0.0f},{2:0.0f}'.format(self.t, self.h, self.p)
        return ret

    def exit(self):
        """Request thread termination."""
        _log.debug('Request to exit')
        self.__running = False

    def __connect(self):
        """Request re-connect, exceptions should bubble up to run loop."""
        _log.debug('Re-connect ypmeteo usb')
        self.__cleanup()
        self.__stat = False
        self.__m = usb.core.find(idVendor=IDVENDOR, idProduct=IDPRODUCT)
        if self.__m is not None:
            if self.__m.is_kernel_driver_active(0):
                _log.debug('Detach kernel driver')
                self.__m.detach_kernel_driver(0)
            self.__m.reset()
            # clear any junk in the read buffer - so that init cmds will send
            try:
                while True:
                    _log.debug('Read stale junk from command buffer')
                    junk = self.__m.read(0x81, 64, 50)
            except usb.core.USBTimeoutError:
                pass
            # send start and conf commands errors here are collected in run
            self.__m.write(0x01, scmd)
            self.__m.write(0x01, ccmd)
            self.__stat = True

    def __cleanup(self):
        """Close current usb connection and clean up used resources."""
        _log.debug('Close and cleanup connection')
        if self.__m is not None:
            try:
                usb.util.dispose_resources(self.__m)
            except:
                _log.warning('Error disposing usb connection resources')
                pass
        self.__m = None
        self.__stat = False
        time.sleep(0.1)  # release thread

    def __read(self):
        bd = bytearray(self.__m.read(0x81, 64))
        _log.debug('Read from usb: %r', bd)
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
                    _log.debug('pktno:%r, stream:%r, size:%r, sb:%r, val:%r',
                               pktno, stream, size, sb, val)
                    if sb == 1:
                        self.t = val
                    elif sb == 2:
                        self.p = val
                    elif sb == 3:
                        self.h = val
            of += size + 2

    def run(self):
        """Called via threading.Thread.start()."""
        _log.debug('Starting')
        if self.__running is None:
            # exit may set this to False before run is called
            self.__running = True
        while self.__running:
            try:
                if self.__stat and self.__m is not None:
                    try:
                        self.__read()
                    except usb.core.USBTimeoutError:
                        pass
                else:
                    self.__connect()
                    _log.debug(u'Re-connect: %r', self.__m)
                    time.sleep(5.0)
            except Exception as e:
                _log.error('%s: %s', e.__class__.__name__, e)
                self.__stat = False
                time.sleep(1.0)
        self.__cleanup()
        _log.debug('Exiting')

    def __enter__(self):
        _log.debug('Enter ctx')
        self.start()
        while not self.connected():
            if self.__ct is not None:
                self.__ct -= 0.1
                if not self.__ct > 0.01:
                    self.exit()
                    raise RuntimeError('Timeout waiting for USB connection')
            time.sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _log.debug('Exit ctx exc_type=%r', exc_type)
        self.exit()
        if exc_type is not None:
            return False  # raise exception
        self.join()
        return True
