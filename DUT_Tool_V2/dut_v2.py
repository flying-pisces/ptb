import os
import time
import re
import numpy as np
import sys
import socket
import serial
import struct
import logging
import datetime
import string
import win32process
import win32event
import pywintypes
import cv as cv2
import pprint
from ctypes import *


class DUTError(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class pancakeDut(object):
    def __init__(self, serialNumber, station_config, operator_interface):
        self._station_config = station_config
        self._operator_interface = operator_interface
        self._verbose = station_config.IS_VERBOSE
        self.is_screen_poweron = False
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._spliter = ','
        self._nvm_data_len = 28
        self._dll = None

    def initialize(self, port, host):
        self.is_screen_poweron = False
        cur = os.path.dirname(os.path.abspath(sys.modules[pancakeDut.__module__].__file__))
        dll_path = os.path.join(cur, 'UDTDLL.dll')
        try:
            self._dll = CDLL(dll_path)
            self._dll.OpenDevice(int(port), c_char_p(str(host).encode('utf-8')))
        except Exception as e:
            raise DUTError(f'Unable to open DUT with {host}, Exp={str(e)}')

        print('DUT Initialised port %s, ip %s. ' % (port, host))
        return True

    def screen_on(self, ntype=0):
        if not self.is_screen_poweron:
            self._dll.PowerOFF()
            time.sleep(0.15)
            recvobj = self._dll.PowerON(ntype)  # type  0 = DSCMode_10P , 1 = DSCMode_100P
            if recvobj is None:
                raise DUTError("Exit power_on because power_on failed.")
            self.is_screen_poweron = True
            self._operator_interface.print_to_console(f"screen on success.\n")
            return True

    def screen_off(self):
        if self.is_screen_poweron:
            self._dll.PowerOFF()
            self._operator_interface.print_to_console(f"screen off success.\n")
            self.is_screen_poweron = False

    def close(self):
        self._operator_interface.print_to_console("Turn Off display................\n")
        if self.is_screen_poweron:
            self._dll.PowerOFF()
        self._operator_interface.print_to_console("Closing DUT.\n")
        self._dll.CloseDevice()
        self.is_screen_poweron = False

    def display_image(self, image, is_ddr_data=False):
        recvobj = self._showImage(image, is_ddr_data)
        time.sleep(self._station_config.DUT_DISPLAYSLEEPTIME)

    def get_version(self):
        """
            get the version of FW.
        """
        res_ver = None
        try:
            self._dll.ReadVersion.restype = c_char_p
            ver = self._dll.ReadVersion()
            res_ver = ver.decode('utf-8')
            self._operator_interface.print_to_console(f"read version return: {res_ver}.\n")
        except Exception as e:
            raise DUTError(f'Get version error: {str(e)}')
        return res_ver

    def _reset(self):
        try:
            self._dll.InitParam()
            self._operator_interface.print_to_console(f"DUT Reset......\n")
        except Exception as e:
            raise DUTError(f'DUT reset Error. exp = {str(e)}')

    def _showImage(self, image_index, is_ddr_img):
        # type: (int, bool) -> str
        try:
            if not is_ddr_img:
                res = self._dll.ShowImage(image_index)
            else:
                res = self._dll.ShowDDRImage(image_index)
            if res != 0:
                raise DUTError(f'Fail to show image f{image_index}, {is_ddr_img}')
        except Exception as e:
            raise DUTError(f'show image fail, except = {str(e)}')

    def _WriteImage(self, filenames: list, isToRGB, iRotationType, nTailor, tailorWidth, tailorHeight, isddr=False, timeout=6000):
        """
        @ Param [in] fileNames; the path array for the burned pictures.
        * @ Param [in] fileNum; the number of burned pictures.
        * @ Param [in] isToRGB; turn the picture to RGB, the default three channels is BGR, true refers to RGB, and false means not turning.
        * @ Param [in] iRotationType; rotate the picture, 1:90 degrees left; 2:90 degrees right; 3: rotate 180 degrees, 4: X image, 5: Y image.
        * @ Param [in] nTailor; supplement the position of the picture data, 0: no; 1: to the right; 2: middle; 3: left.
        * @ Param [in] tailorWidth; complete the picture width, if nTailor=0, the change parameter is invalid.
        * @ Param [in] tailorHeight; complete the picture height, if nTailor=0, the change parameter is invalid.
        * @ Param [in] timeout; timeout time in milliseconds.
        * @return Return to the status
        """

        if not isinstance(filenames, list):
            raise DUTError(f'args err.')
        file_nums = len(filenames)
        c_files = (c_char_p * file_nums)()
        for file in range(file_nums):
            c_files[file] = filenames[file].encode('utf-8')
        try:
            res = -1
            if not isddr:
                res = self._dll.WriteImageToEMMC(c_files, file_nums, c_bool(isToRGB), iRotationType, nTailor, tailorWidth, tailorHeight, timeout)
            else:
                res = self._dll.WriteImageToDDR(c_files, file_nums, c_bool(isToRGB), iRotationType, nTailor, tailorWidth, tailorHeight, timeout)
            if res != 0:
                self._operator_interface.print_to_console(f"write image Failed, return: {res}\n")
                return False
        except Exception as e:
            raise DUTError(f'write image to EMMC Err, exp = {str(e)}')

        self._operator_interface.print_to_console("write image success................\n")
        return True

    def _ReadEeprom(self, addr, length):
        val = None
        try:

            self._dll.ReadEeprom.restype = c_char_p
            val = self._dll.ReadEeprom(addr, length)
            print('val: ', val.decode('utf-8'), type(val))

        except Exception as e:
            raise DUTError(f'read Eeprom Error, exp= {str(e)}')

        self._operator_interface.print_to_console(f"read Eeprom {addr}-{length}, value= {val}................\n")
        return val

    def _WriteEeprom(self, addr, value):
        try:
            self._dll.WriteEeprom(c_short(addr), c_int(value))
        except Exception as e:
            raise DUTError(f'read Eeprom Error, exp= {str(e)}')
        self._operator_interface.print_to_console("write Eeprom finished................\n")

    def _saveEditBMP(self, file, targetFile, isToRGB, iRotationType, nTailor, tailorWidth, tailorHeight):
        c_file = c_char_p(file.encode('utf-8'))
        c_targetFile = c_char_p(targetFile.encode('utf-8'))
        success = False
        try:
            res = self._dll.SaveEditBMP(c_file, c_targetFile, isToRGB, iRotationType, nTailor, tailorWidth, tailorHeight)
            if res == 0:
                self._operator_interface.print_to_console("save edit Bmp success.\n")
                success = True
            else:
                self._operator_interface.print_to_console(f"save edit Bmp failed, return {res}.................\n")
        except Exception as e:
            raise DUTError(f'save edit BMP Error, exp= {str(e)}')
        return success

    def _SetDeviceIpAddress(self, addr):
        """
        * Device must be open with the OpenDevice function before using this function
        * After using this function, the CloseDevice function must close the device and wait for the device to restart.
        * @ Param [in] address; do not use 1 or 255, IP number: 192.168.21.address
        * @return Returns the version
        *@par instance:
        * @code
        *		OpenDevice(6000,"192.168.21.132");
        *       SetDeviceIpAddress(134);
        *       CloseDevice();
        * @endcode
        """
        try:
            self._dll.SetDeviceIpAddress(addr)
            self._operator_interface.print_to_console(f"set ip to {addr} success......\n")
        except Exception as e:
            raise DUTError(f' set ip error, exp= {str(e)}')

    # </editor-fold>


def print_to_console(self, msg):
    pass


if __name__ == "__main__":
    class cfgstub(object):
        pass

    station_config = cfgstub()
    station_config.DUT_DISPLAYSLEEPTIME = 0.1

    import sys
    import types

    sys.path.append(r'..\..')

    station_config.print_to_console = types.MethodType(print_to_console, station_config)
    station_config.IS_VERBOSE = True

    the_unit = pancakeDut(station_config, station_config, station_config)
    the_unit.initialize(6000, '192.168.21.132')

    try:
        for idx in range(0, 2):
            is_to_ddr = idx % 2 == 1  # Save the image to DDR or EMMC ?
            print(f'Loop ---> Idx = {idx}, IS_TO_DDR = {is_to_ddr}')
            # !!! image format: 1800 * 1920, bit depth: 24, format: bmp
            # !!! make sure the filename of image is simple enough.
            pics = []
            if os.path.exists('img'):
                for c in os.listdir('img'):
                    if c.endswith(".bmp") or c.endswith('.png'):
                        pics.append(os.path.abspath(r'img\{}'.format(c)))

            print('pic - count {0}'.format(len(pics)))
            if len(pics) > 0:
                the_unit._WriteImage(pics, False, 0, 0, 2064, 2208, is_to_ddr)

            time.sleep(5)
            the_unit.screen_on()
            the_unit.get_version()

            # # the_unit._WriteEeprom(1, 2)
            # time.sleep(2)
            # the_unit._ReadEeprom(4, 4)

            for c in range(0, len(pics)):  # show image in DDR
                print(f'display image {c} =================')
                the_unit.display_image(c, is_to_ddr)
                time.sleep(1.5)

            time.sleep(2)
            the_unit.screen_off()

    except Exception as e:
        print(e)
    finally:
        time.sleep(2)
        the_unit.close()

