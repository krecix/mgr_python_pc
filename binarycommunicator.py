#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 16 16:19:28 2021

@author: krzysztof
"""

import zlib

byteOrder = 'little'


class BinaryCommunicator():
    
    def __init__(self, serial):
        
        self.serial = serial
        
        self.serial.close()
        self.serial.open()
    
    def openSerial(self):
        self.serial.close()
        self.serial.open()
        
    def closeSerial(self):
        self.serial.close()
    
    def receiveData(self):
        
        returnMsg = self.serial.read(size=1)
        
        startByte = int.from_bytes(returnMsg, byteOrder)
    
        if startByte == 1:
            returnMsg = self.serial.read(size=4)
        else:
            return None
        length = int.from_bytes(returnMsg, byteOrder)
        
        returnMsg = self.serial.read(size=length)
        msg = returnMsg
        
        returnMsg = self.serial.read(size=4)
        crcReceived = int.from_bytes(returnMsg, byteOrder)
        crc = zlib.crc32(msg) & 0xffffffff
        
        returnMsg = self.serial.read(size=1)
        stopByte = int.from_bytes(returnMsg, byteOrder)
        
        if stopByte == 1 and (crc == crcReceived):
            return msg
        else:
            return None
    
    def sendData(self, data):
        
        #Start byte
        byteArray = bytearray(int(1).to_bytes(1, byteOrder))
        
        #Message length
        byteArray += len(data).to_bytes(4, byteOrder)
        
        #Message
        byteArray += data
        
        #CRC32
        crc = zlib.crc32(data) & 0xffffffff
        byteArray += crc.to_bytes(4, byteOrder)
        
        #Stop byte
        byteArray += bytearray(int(1).to_bytes(1, byteOrder))
        
        self.serial.write(byteArray)
        
        return self.receiveData()
        
        
            
        
        