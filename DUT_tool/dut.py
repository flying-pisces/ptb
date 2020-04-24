import os
import time
import re
import numpy as np
import sys
import socket
import serial
import struct
import logging
import time
import datetime
import string
import win32process
import win32event
import pywintypes
import pprint


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
        # hardware_station_common.test_station.dut.DUT.__init__(self, serialNumber, station_config, operatorInterface)
        self.first_boot = True
        self._verbose = station_config.IS_VERBOSE
        self.is_screen_poweron = False
        self._serial_port = None # type: serial.Serial
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._start_delimiter = "$"
        self._end_delimiter = b'\r\n'
        self._spliter = ','
        self._renderImgTool = os.path.join(os.getcwd(), r'CambriaToos\exe\CambriaTools-cmd.exe')

    def initialize(self):
        self.is_screen_poweron = False
        self._serial_port = serial.Serial(self._station_config.DUT_COMPORT,
                                          baudrate=115200,
                                          bytesize=serial.EIGHTBITS,
                                          parity=serial.PARITY_NONE,
                                          stopbits=serial.STOPBITS_ONE,
                                          rtscts=False,
                                          xonxoff=False,
                                          dsrdtr=False,
                                          timeout=1,
                                          writeTimeout=None,
                                          interCharTimeout=None)
        if not self._serial_port:
            raise DUTError('Unable to open DUT port : %s' % self._station_config.DUT_COMPORT)
            return False
        else:
            self.first_boot = True
            if self._verbose:
                print('DUT %s Initialised. ' % self._station_config.DUT_COMPORT)
            return True
        return False

    def connect_display(self, display_cycle_time=2, launch_time=4):
        if self.first_boot:
            self.first_boot = False
            self._power_off()
            time.sleep(0.5)
            recvobj = self._power_on()
            if recvobj is None:
                raise RuntimeError("Exit power_on because can't receive any data from dut.")
            else:
                self.is_screen_poweron = True
                if recvobj[0] != '0000':
                    raise DUTError("Exit power_off because rev err msg. Msg = {}".format(recvobj))
                return True
            time.sleep(display_cycle_time)
        return True

    def screen_on(self):
        if not self.is_screen_poweron:
            self._power_off()
            time.sleep(0.5)
            recvobj = self._power_on()
            if recvobj is None:
                raise RuntimeError("Exit power_on because can't receive any data from dut.")
            else:
                self.is_screen_poweron = True
                if recvobj[0] != '0000':
                    raise DUTError("Exit power_off because rev err msg. Msg = {}".format(recvobj))
                return True

    def screen_off(self):
        if self.is_screen_poweron:
            self._power_off()
            self.is_screen_poweron = False

    def close(self):
        self._operator_interface.print_to_console("Turn Off display................\n")
        if self.is_screen_poweron:
            self._power_off()
        self._operator_interface.print_to_console("Closing DUT by the communication interface.\n")
        if self._serial_port is not None:
            self._serial_port.close()
            self._serial_port = None

    def display_color(self, color=(255,255,255)): #  (r,g,b)
        if self.is_screen_poweron:
            recvobj = self._setColor(color)
            if recvobj is None:
                raise RuntimeError("Exit display_color because can't receive any data from dut.")
            elif int(recvobj[0]) != 0x00:
                raise RuntimeError("Exit display_color because rev err msg. Msg = {}".format(recvobj))
        time.sleep(self._station_config.DUT_DISPLAYSLEEPTIME)

    def display_image(self, image, is_ddr_data=False):
        recvobj = self._showImage(image, is_ddr_data)
        if recvobj is None:
            raise RuntimeError("Exit disp_image because can't receive any data from dut.")
        elif int(recvobj[0]) != 0x00:
            raise DUTError("Exit disp_image because rev err msg. Msg = {}".format(recvobj))
        time.sleep(self._station_config.DUT_DISPLAYSLEEPTIME)

    def vsync_microseconds(self):
        recvobj = self._vsyn_time()
        if recvobj is None:
            raise RuntimeError("Exit display_color because can't receive any data from dut.")
        else:
            grpt = re.match(r'(\d*[\.]?\d*)', recvobj[1])
            grpf = re.match(r'(\d*[\.]?\d*)', recvobj[2])
            if grpf is None or grpt is None:
                raise RuntimeError("Exit display_color because rev err msg. Msg = {}".format(recvobj))
            return string.atof(grpt.group(0))

    def get_version(self):
        return self._version("mcu")

    def render_image(self, pics):
        """
            call utils to render images to ddr
        :type pics: []
        """
        if isinstance(pics, list):
            cmd = os.path.basename(self._renderImgTool) + ' -push ' + \
                  ' '.join([os.path.abspath(c) for c in pics])
            return self._timeout_execute(cmd, len(pics) * self._station_config.DUT_RENDER_ONE_IMAGE_TIMEOUT)

    def reboot(self):
        delay_seconds = 40
        if hasattr(self._station_config, 'COMMAND_DISP_REBOOT_DLY'):
            delay_seconds = self._station_config.COMMAND_DISP_REBOOT_DLY
        sw = datetime.datetime.now()

        recvobj = self._reboot()
        self.is_screen_poweron = False
        if recvobj is None:
            raise RuntimeError("Fail to reboot because can't receive any data from dut.")
        elif int(recvobj[0]) != 0x00:
            raise DUTError("Fail to reboot because rev err msg. Msg = {}".format(recvobj))

        while True:
            dt = datetime.datetime.now()
            if (dt - sw).total_seconds() > delay_seconds:
                raise DUTError('Fail to reboot because waiting msg timeout {0:4f}s. '.format((dt - sw).total_seconds()))
            response = self._serial_port.readline()
            if response is None or len(response) <= 0:
                time.sleep(1)
                if self._verbose:
                    print('.')
                continue
            recvobj = self._prase_respose('System OK', response)
            if int(recvobj[0]) == 0x00:
                if self._verbose:
                    print('Reboot system successfully . Elapse time {0:4f} s.'.format((dt - sw).total_seconds()))
                break
            else:
                raise DUTError("Fail to reboot because rev err msg. Msg = {}".format(recvobj))

    # <editor-fold desc='InternalCommand'>

    def _timeout_execute(self, cmd, timeout=0):
        if timeout == 0:
            timeout = win32event.INFINITE
        cwd = os.getcwd()
        res = -1
        try:
            si = win32process.STARTUPINFO()
            render_img_path = os.path.dirname(self._renderImgTool)
            os.chdir(render_img_path)
            # si.dwFlags |= win32process.STARTF_USESHOWWINDOW

            handle = win32process.CreateProcess(None, cmd, None, None, 0, win32process.CREATE_NO_WINDOW,
                                                None, None, si)
            rc = win32event.WaitForSingleObject(handle[0], timeout)
            if rc == win32event.WAIT_FAILED:
                res = -1
            elif rc == win32event.WAIT_TIMEOUT:
                try:
                    win32process.TerminateProcess(handle[0], 0)
                except pywintypes.error as e:
                    raise DUTError('exectue {} timeout :{}'.format(cmd, e))
                if rc == win32event.WAIT_OBJECT_0:
                    res = win32process.GetExitCodeProcess(handle[0])
            else:
                res = 0
        finally:
            os.chdir(cwd)
        if res != 0:
            raise DUTError('fail to exec {} res :{}'.format(cmd, res))
        return res

    def _write_serial_cmd(self, command):
        cmd = '$c.{}\r\n'.format(command)
        if self._verbose:
            print('send command ----------> {}'.format(cmd))

        self._serial_port.flush()
        self._serial_port.write(cmd.encode('utf-8'))

    def _read_response(self, timeout=5):
        response = []
        line_in = b''
        tim = time.time()
        while (not re.search(self._end_delimiter, line_in, re.IGNORECASE)
               and (time.time() - tim < timeout)):
            line_in = self._serial_port.readline()
            if line_in != b'':
                response.append(line_in.decode())
        if self._verbose and len(response) > 1:
            pprint.pprint(response)
        return response

    def _vsyn_time(self):
        self._write_serial_cmd(self._station_config.COMMAND_DISP_VSYNC)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_VSYNC, response)

    def _help(self):
        self._write_serial_cmd(self._station_config.COMMAND_DISP_HELP)
        time.sleep(1)
        response = self._read_response()
        if self._verbose:
            print(response)
        value = []
        for item in response[0:len(response)-1]:
            value.append(item)
        return value

    def _version(self, model_name):
        self._write_serial_cmd("%s,%s"%(self._station_config.COMMAND_DISP_VERSION,model_name))
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_VERSION, response)

    def _get_boardId(self):
        self._write_serial_cmd(self._station_config.COMMAND_DISP_GETBOARDID)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_GETBOARDID, response)

    def _prase_respose(self, command, response):

        if self._verbose:
            print("command : {},,,{}".format(command, response))

        if response is None:
            return None
        cmd1 = command.split(self._spliter)[0]
        respstr = ''.join(response).upper()
        cmd = ''.format(cmd1).upper()
        if cmd not in respstr:
            return None
        values = respstr.split(self._spliter)
        if len(values) == 1:
            raise RuntimeError('display ctrl rev data format error. <- ' + respstr)
        return values[1:]

    def _power_on(self):
        self._write_serial_cmd(self._station_config.COMMAND_DISP_POWERON)
        time.sleep(self._station_config.COMMAND_DISP_POWERON_DLY)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_POWERON, response)

    def _power_off(self):
        self._write_serial_cmd(self._station_config.COMMAND_DISP_POWEROFF)
        time.sleep(self._station_config.COMMAND_DISP_POWEROFF_DLY)
        response = self._read_response()
        # return self._prase_respose(self._station_config.COMMAND_DISP_POWEROFF, response)

    def _reset(self):
        self._write_serial_cmd(self._station_config.COMMAND_DISP_RESET)
        time.sleep(self._station_config.COMMAND_DISP_RESET_DLY)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_RESET, response)

    def _showImage(self, image_index, is_ddr_img):
        # type: (int, bool) -> str
        command = ''
        if isinstance(image_index, str):
            command = '{},{}'.format(self._station_config.COMMAND_DISP_SHOWIMAGE, image_index)
        elif isinstance(image_index, int):
            if is_ddr_img:
                image_index = 0x20 + image_index
            command = '{},{}'.format(self._station_config.COMMAND_DISP_SHOWIMAGE, hex(image_index))
        self._write_serial_cmd(command)
        time.sleep(self._station_config.COMMAND_DISP_SHOWIMG_DLY)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_SHOWIMAGE, response)

    def _setColor(self, c=(255, 255, 255)):
        command = '{0},0x{1[0]:02X},0x{1[1]:02X},0x{1[2]:02X}'.format(self._station_config.COMMAND_DISP_SETCOLOR, c)
        self._write_serial_cmd(command)
        time.sleep(0.02)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_SETCOLOR, response)

    def _MIPI_read(self, reg, typ):
        command = '{0},{1},{2}'.format(self._station_config.COMMAND_DISP_READ, reg, typ)
        self._write_serial_cmd(command)
        # time.sleep(1)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_READ, response)

    def _MIPI_write(self, reg, typ, val):
        command = '{0},{1},{2},{3}'.format(self._station_config.COMMAND_DISP_WRITE, reg, typ, val)
        self._write_serial_cmd(command)
        #time.sleep(1)
        response = self._read_response()
        return self._prase_respose(self._station_config.COMMAND_DISP_WRITE, response)

    def _reboot(self):
        cmd = 'Reboot'
        if hasattr(self._station_config, 'COMMAND_REBOOT'):
            cmd = self._station_config.COMMAND_REBOOT
        self._write_serial_cmd(cmd)
        response = self._read_response()
        return self._prase_respose(cmd, response)

    # </editor-fold>

def print_to_console(self, msg):
    pass

if __name__ == "__main__" :

    class cfgstub(object):
        pass

    station_config = cfgstub()
    station_config.DUT_COMPORT = "COM3"
    station_config.DUT_DISPLAYSLEEPTIME = 0.1
    station_config.DUT_RENDER_ONE_IMAGE_TIMEOUT = 0
    station_config.COMMAND_DISP_HELP = "$c.help"
    station_config.COMMAND_DISP_VERSION_GRP = ['mcu', 'hw', 'fpga']
    station_config.COMMAND_DISP_VERSION = "Version"
    station_config.COMMAND_DISP_GETBOARDID = "getBoardID"
    station_config.COMMAND_DISP_POWERON = "DUT.powerOn,FPGA_compressMode"
    # COMMAND_DISP_POWERON = "DUT.powerOn,SSD2832_BistMode"
    station_config.COMMAND_DISP_POWEROFF = "DUT.powerOff"
    station_config.COMMAND_DISP_RESET = "Reset"
    station_config.COMMAND_DISP_SETCOLOR = "SetColor"
    station_config.COMMAND_DISP_SHOWIMAGE = "ShowImage"
    station_config.COMMAND_DISP_READ = "MIPI.Read"
    station_config.COMMAND_DISP_WRITE = "MIPI.Write"
    station_config.COMMAND_DISP_2832WRITE = "t.2832_MIPI_WRITE"
    station_config.COMMAND_DISP_VSYNC = "REFRESHRATE"
    station_config.COMMAND_DISP_POWERON_DLY = 1.5
    station_config.COMMAND_DISP_RESET_DLY = 1
    station_config.COMMAND_DISP_SHOWIMG_DLY = 0.5
    station_config.COMMAND_DISP_POWEROFF_DLY = 0.2

    import sys
    import types
    sys.path.append(r'..\..')

    station_config.print_to_console = types.MethodType(print_to_console, station_config)
    station_config.IS_VERBOSE = True

    the_unit = pancakeDut(station_config, station_config, station_config)
    for idx in range(0, 100):

        print('Loop ---> {}'.format(idx))

        pics = []
        if os.path.exists('img'):
            for c in os.listdir('img'):
                if c.endswith(".bmp"):
                    pics.append(r'img\{}'.format(c))

        print('pic - count {0}'.format(len(pics)))

        # the_unit.render_image(pics)
        the_unit.initialize()
        try:
            # the_unit.reboot()
            the_unit.connect_display()
            time.sleep(0.5)
            # the_unit.screen_on()
            # time.sleep(1)
            # the_unit.display_color()
            # time.sleep(1)
            # print(the_unit.vsync_microseconds())
            for c in [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)]:
                the_unit.display_color(c)
                time.sleep(0.1)

            # for c in range(0, len(pics)): # DDR Image
            for c in range(0, 5):
                the_unit.display_image(c, False)
                time.sleep(0.5)
            the_unit.screen_off()
        except Exception as e:
            print(e)
        finally:
            time.sleep(2)
            the_unit.close()