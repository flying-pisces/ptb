#pragma once
#define UDT_API __declspec(dllexport)

extern "C"   //interface in output dll used by the program
{
	
	/**
	* @brief Open the device \ n
	* After the file opens successfully, it must be closed using the closeDevice function
	* @ Param [in] portName); the port number of the TCP server
	* @ Param [in] ipaddress); the IP address of the TCP server
	* @return Return to the device-on state
	* -1 means failed to open the device, 0 means successful to open the device
	*@par instance:
	* @code
	*        int ret = OpenDevice(6000,"192.168.21.132");
	* @endcode
	*/
	UDT_API  int OpenDevice(int portName, char* ipaddress);


	/**
	* @brief Close the device, openDevice open the device \ n
	* @return Return to the device-off state
	* -1 indicates device closure failure, and 0 means successful device closure
	*@par instance:
	* @code
	*        CloseDevice();
	* @endcode
	*/
	UDT_API  void CloseDevice();

	/**
	* @brief Burn pictures inside the device EMMC \ n
	* @ Param [in] fileNames; the path array for the burned pictures.
	* @ Param [in] fileNum; the number of burned pictures.
	* @ Param [in] isToRGB; turn the picture to RGB, the default three channels is BGR, true refers to RGB, and false means not turning.
	* @ Param [in] iRotationType; rotate the picture, 1:90 degrees left; 2:90 degrees right; 3: rotate 180 degrees, 4: X image, 5: Y image.
	* @ Param [in] nTailor; supplement the position of the picture data, 0: no; 1: to the right; 2: middle; 3: left.
	* @ Param [in] tailorWidth; complete the picture width, if nTailor=0, the change parameter is invalid.
	* @ Param [in] tailorHeight; complete the picture height, if nTailor=0, the change parameter is invalid.
	* @ Param [in] timeout; timeout time in milliseconds.
	* @return Return to the status
	* 0 means burning successfully, -1 failed to open the picture, -2 burning picture is not in BMP format, -3 failed to send picture information, -4 fails to clear the cache area, -5 failed to send image data, -6 pictures failed to write data, -7 image confirmation failed.
	*@par instance:
	* @code
	*		char* filenames[2] = { "D:\\2.bmp","D:\\3.bmp"};
	*        int ret = WriteImageToEMMC(filenames,0,false,0,0,1900,1920,6000);
	* @endcode
	*/

	UDT_API  int WriteImageToEMMC(char *filenames[1024], const int fileNum, bool isToRGB, int iRotationType, int nTailor, int tailorWidth, int tailorHeight, int timeout = 6000);

	/**
	* @brief Burn pictures to inside the device DDR \ n
	* @ Param [in] fileNames; the path array for the burned pictures.
	* @ Param [in] fileNum; the number of burned pictures.
	* @ Param [in] isToRGB; turn the picture to RGB, the default three channels is BGR, true refers to RGB, and false means not turning.
	* @ Param [in] iRotationType; rotate the picture, 1:90 degrees left; 2:90 degrees right; 3: rotate 180 degrees, 4: X image, 5: Y image.
	* @ Param [in] nTailor; supplement the position of the picture data, 0: no; 1: to the right; 2: middle; 3: left.
	* @ Param [in] tailorWidth; complete the picture width, if nTailor=0, the change parameter is invalid.
	* @ Param [in] tailorHeight; complete the picture height, if nTailor=0, the change parameter is invalid.
	* @ Param [in] timeout; timeout time in milliseconds.
	* @return Return to the status
	* 0 means burning successfully, -1 failed to open the picture, -2 burning picture is not in BMP format, -3 failed to send picture information, -4 fails to clear the cache area, -5 failed to send image data, -6 pictures failed to write data, -7 image confirmation failed.
	*@par instance:
	* @code
	*		char* filenames[2] = { "D:\\2.bmp","D:\\3.bmp"};
	*        int ret = WriteImageToDDR(filenames,0,false,0,0,1900,1920,6000);
	* @endcode
	*/

	UDT_API  int WriteImageToDDR(char *filenames[1024], const int fileNum, bool isToRGB, int iRotationType, int nTailor, int tailorWidth, int tailorHeight, int timeout);

	/**
	* @brief Display the pictures inside the EMMC on the device screen \ n
	* @ Param [in] index; displays the serial number of the picture.
	* @return Return to the status
	* -1 indicates display failure, and 0 indicates display success
	*@par instance:
	* @code
	*        int ret = ShowImage(0);
	* @endcode
	*/

	UDT_API int ShowImage(const int index);

	/**
	* @brief Display the picture in the DDR on the device screen \ n
	* @ Param [in] index; displays the serial number of the picture.
	* @return Return to the status
	* -1 indicates display failure, and 0 indicates display success
	*@par instance:
	* @code
	*        int ret = ShowDDRImage(0);
	* @endcode
	*/

	UDT_API int ShowDDRImage(const int index);

	/**
	* @brief Power on the screen \ n
	* @ Param [in] ntype; Poweron type  0 = DSCMode_10P , 1 = DSCMode_100P.
	* @return No return status
	*@par instance:
	* @code
	*         PowerON(0);
	* @endcode
	*/

	UDT_API void  PowerON(const int ntype);

	/**
	* @brief Screen power \ n
	* @return No return status
	*@par instance:
	* @code
	*        PowerOFF();
	* @endcode
	*/

	UDT_API void PowerOFF();

	/**
	* @brief Read the mcu version \ n
	* @return Returns the version
	*@par instance:
	* @code
	*       char*ver = ReadVersion();
	* @endcode
	*/
	UDT_API char* ReadVersion();

	/**
	* @brief Read the Eeprom \ n
	* @return Return the value of the eeprom
	*@par instance:
	* @code
	*       char*eeprom = ReadEeprom(1,2);
	* @endcode
	*/
	UDT_API char* ReadEeprom(unsigned short addr, unsigned char len);

	/**
	* @brief Write the Eeprom \ n
	* @return 
	*@par instance:
	* @code
	*       WriteEeprom(1,2);
	* @endcode
	*/
	UDT_API void WriteEeprom(unsigned short addr, unsigned int value);

	/**
	* @brief Initialization parameter \ n
	*After using this function, the CloseDevice function must close the device and wait for the device to restart.
	* @return 
	*@par instance:
	* @code
	*       InitParam();
	*		CloseDevice();
	* @endcode
	*/
	UDT_API void InitParam();

	/**
	* @brief Save the modified image, for test use only \ n
	* @ Param [in] sourcefile; the path of the source image.
	* @ Param [in] destfile; the path of the destination picture.
	* @ Param [in] isToRGB; turn the picture to RGB, the default three channels is BGR, true refers to RGB, and false means not turning.
	* @ Param [in] iRotationType; rotate the picture, 1:90 degrees left; 2:90 degrees right; 3: rotate 180 degrees, 4: X image, 5: Y image.
	* @ Param [in] nTailor; supplement the position of the picture data, 0: no; 1: to the right; 2: middle; 3: left.
	* @ Param [in] tailorWidth; complete the picture width, if nTailor=0, the change parameter is invalid.
	* @ Param [in] tailorHeight; complete the picture height, if nTailor=0, the change parameter is invalid.
	* @return Return to the status
	* -1 is a failure and 0 is a success
	*@par instance:
	* @code
	*        int ret = SaveEditBMP(¡°D:\123.bmp¡±,"D:\2.bmp",false,0,0,1900,1920);
	* @endcode
	*/
	UDT_API int SaveEditBMP(char *sourcefile, char *destfile, bool isToRGB, int iRotationType, int nTailor, int tailorWidth, int tailorHeight);
	

	/**
	* @brief Reset the IP address \ n
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
	*/
	UDT_API void SetDeviceIpAddress(int address);
}

