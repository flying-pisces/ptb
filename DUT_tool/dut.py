import os
import time
import re
import sys
import socket
import serial
import struct
import logging
import time
import string
import win32process
import win32event
import pywintypes

DUT_COMPORT = "COM3"
DUT_DISPLAYSLEEPTIME = 0.1
DUT_RENDER_ONE_IMAGE_TIMEOUT = 0
COMMAND_DISP_HELP = "$c.help"
COMMAND_DISP_VERSION_GRP=['mcu','hw','fpga']
COMMAND_DISP_VERSION = "Version"
COMMAND_DISP_GETBOARDID = "getBoardID"
COMMAND_DISP_POWERON = "DUT.powerOn,FPGA_compressMode"
# COMMAND_DISP_POWERON = "DUT.powerOn,SSD2832_BistMode"
COMMAND_DISP_POWEROFF = "DUT.powerOff"
COMMAND_DISP_RESET = "Reset"
COMMAND_DISP_SETCOLOR = "SetColor"
COMMAND_DISP_SHOWIMAGE = "ShowImage"
COMMAND_DISP_READ = "MIPI.Read"
COMMAND_DISP_WRITE = "MIPI.Write"
COMMAND_DISP_2832WRITE = "t.2832_MIPI_WRITE"
COMMAND_DISP_VSYNC="REFRESHRATE"

COMMAND_DISP_POWERON_DLY = 1.5
COMMAND_DISP_RESET_DLY = 1
COMMAND_DISP_SHOWIMG_DLY = 1
COMMAND_DISP_POWEROFF_DLY = 0.2

class DUTError(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

class pancakeDut():
    def __init__(self, serialNumber):
        self.first_boot = True
        self.is_screen_poweron = False
        self._serial_number = serialNumber
        self._serial_port = None
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._start_delimiter = "$"
        self._end_delimiter = '\r\n'
        self._spliter = ','
        self._renderImgTool = os.path.join(os.getcwd(), r'CambriaToos\exe\CambriaTools-cmd.exe')

    def initialize(self):
        self.is_screen_poweron = False
        self._serial_port = serial.Serial(self._serial_number,
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
            raise DUTError('Unable to open DUT port : %s' % self._serial_number)
            return False
        else:
            print ('DUT %s Initialised. ' % self._serial_port)
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
                print ("Exit power_on because can't receive any data from dut.")
            else:
                self.is_screen_poweron = True
                if recvobj[0] != '0000':
                    raise DUTError("Exit power_off because rev err msg. Msg = {}".format(recvobj))
                return True

    def screen_off(self):
        if self.is_screen_poweron:
            recvobj = self._power_off()
            if recvobj is None:
                raise RuntimeError("Exit power_off because can't receive any data from dut.")
            elif int(recvobj[0]) != 0x00:
                raise DUTError("Exit power_off because rev err msg. Msg = {}".format(recvobj))
            else:
                self.is_screen_poweron = False

    def close(self):
        print ("Turn Off display................\n")
        if self.is_screen_poweron:
            self._power_off()
        print ("Closing DUT by the communication interface.\n")
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
        time.sleep(DUT_DISPLAYSLEEPTIME)

    def display_image(self, image, is_ddr_data=False):
        recvobj = self._showImage(image, is_ddr_data)
        if recvobj is None:
            raise RuntimeError("Exit disp_image because can't receive any data from dut.")
        elif int(recvobj[0]) != 0x00:
            raise DUTError("Exit disp_image because rev err msg. Msg = {}".format(recvobj))
        time.sleep(DUT_DISPLAYSLEEPTIME)

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
            return self._timeout_execute(cmd, len(pics) * DUT_RENDER_ONE_IMAGE_TIMEOUT)

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
        finally:
            os.chdir(cwd)
        print ('_timeout_execute ')
        return res

    def _write_serial(self, input_bytes):
        bytes_written = self._serial_port.write(input_bytes)
        self._serial_port.flush()
        return bytes_written

    def _write_serial_cmd(self, command):
        cmd = '$c.{}\r\n'.format(command)
        self._serial_port.write(str.encode(cmd))
        self._serial_port.flush()

    def _read_response(self):
        response = []
        while True:
            line_in = self._serial_port.readline()
            if line_in != b'':
                response.append(line_in.decode('utf-8'))
            else:
                break
        print ("<--- {}".format(response))
        return response

    def _vsyn_time(self):
        self._write_serial_cmd(COMMAND_DISP_VSYNC)
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_VSYNC, response)

    def _help(self):
        self._write_serial_cmd(COMMAND_DISP_HELP)
        time.sleep(1)
        response = self._read_response()
        print (response)
        value = []
        for item in response[0:len(response)-1]:
            value.append(item)
        return value

    def _version(self, model_name):
        self._write_serial_cmd("%s,%s"%(COMMAND_DISP_VERSION,model_name))
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_VERSION, response)

    def _get_boardId(self):
        self._write_serial_cmd(COMMAND_DISP_GETBOARDID)
        time.sleep(1)
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_GETBOARDID, response)

    def _prase_respose(self, command, response):

        print ("command : {},,,{}".format(command, response))

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


        return  values[1:]

    def _power_on(self):
        self._write_serial_cmd(COMMAND_DISP_POWERON)
        time.sleep(COMMAND_DISP_POWERON_DLY)
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_POWERON, response)

    def _power_off(self):
        self._write_serial_cmd(COMMAND_DISP_POWEROFF)
        time.sleep(COMMAND_DISP_POWEROFF_DLY)
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_POWEROFF, response)

    def _reset(self):
        self._write_serial_cmd(COMMAND_DISP_RESET)
        time.sleep(COMMAND_DISP_RESET_DLY)
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_RESET, response)

    def _showImage(self, imageindex, is_ddr_img):
        # type: (int, bool)->str
        command = ''
        if isinstance(imageindex, str):
            command ='{},{}'.format(COMMAND_DISP_SHOWIMAGE, imageindex)
        elif isinstance(imageindex, int):
            if is_ddr_img:
                imageindex = 0x20 + imageindex
            command = '{},{}'.format(COMMAND_DISP_SHOWIMAGE, hex(imageindex))
        self._write_serial_cmd(command)
        time.sleep(COMMAND_DISP_SHOWIMG_DLY)
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_SHOWIMAGE, response)

    def _setColor(self, c = (255,255,255)):
        command = '{0},0x{1[0]:X},0x{1[1]:X},0x{1[2]:X}'.format(COMMAND_DISP_SETCOLOR, c)
        self._write_serial_cmd(command)
        time.sleep(1)
        response = self._read_response()
        return self._prase_respose(COMMAND_DISP_SETCOLOR, response)

    # </editor-fold>

if __name__ == "__main__" :
    import sys
    import types
    import logging
    the_unit = None

    try:
        the_unit = pancakeDut(DUT_COMPORT)
        the_unit.initialize()

        for idx in range(0, 2):
            print ('Loop ---> {}'.format(idx))
            pics = []

            the_unit.connect_display()
            # for c in [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)]:
            for c in range(0, 23):
                the_unit.display_image(c, True)
                # the_unit.display_color(c)
                time.sleep(0.1)
            the_unit.screen_off()
    except DUTError as e:
        print (e.message)
    finally:
        if the_unit is not None:
            time.sleep(2)
            the_unit.close()
