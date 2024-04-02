#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 25 18:01:23 2021

@author: krzysztof
"""

import struct
import sys
from calculations import parse_measurements

byteOrder = 'little'

class VibrationUnit():
    
    def __init__(self, binaryCommunicator):
        self.binaryCommunicator = binaryCommunicator
    
    def __prepareLoadingPatternMsg(self, pattern):
        messageEncoded = 0x0C
        messageEncoded = messageEncoded.to_bytes(1, byteOrder)
        
        messageEncoded += len(pattern).to_bytes(4, byteOrder)
        for element in pattern:
            if element['c'] == 'g':
                messageEncoded += int(0x01).to_bytes(1, byteOrder)
                messageEncoded += element['p'].to_bytes(1, byteOrder)
            else:
                messageEncoded += int(0x02).to_bytes(1, byteOrder)
                messageEncoded += element['t'].to_bytes(2, byteOrder)
                
        return messageEncoded
        
    def loadPattern(self, pattern):
        self.binaryCommunicator.openSerial()
        print("Loading pattern to device...")
        message = self.__prepareLoadingPatternMsg(pattern)
        
        receivedMsg = self.binaryCommunicator.sendData(message)
        if (receivedMsg == None):
            print("Returned message is None")
            sys.exit()

        print("Pattern status:", receivedMsg[1])
        self.binaryCommunicator.closeSerial()
        
    def __prepareCheckPID(self, P, I, D):
        messageEncoded = 0x0E
        messageEncoded = messageEncoded.to_bytes(1, byteOrder)
        # !f is littleEndian
        messageEncoded += bytearray(struct.pack("!f", P))  
        messageEncoded += bytearray(struct.pack("!f", I))  
        messageEncoded += bytearray(struct.pack("!f", D)) 
        
        return messageEncoded
    
    def __prepareCheckSingleParameter(self, U):
        messageEncoded = 0x0D
        messageEncoded = messageEncoded.to_bytes(1, byteOrder)
        # !f is littleEndian
        messageEncoded += bytearray(struct.pack("!f", U))  
        
        return messageEncoded
    
    def __prepareMeasurementFromCheckPID(self, rawMeasurement):
        data = rawMeasurement[2:]
        pointZero = data[:2]
        pointZero = int.from_bytes(pointZero, 'little')
        data = data[2:]
        length = int((len(data)))
        
        values = []
        for i in range(0, length, 2):
            value = int.from_bytes(bytearray([data[i], data[i+1]]), byteOrder)
            values += [float(value)]
        
        print(f'Number of samples: {len(values)}')

        return values

    def __prepareMeasurementFromCheckSingleParameter(self, rawMeasurement):
        data = rawMeasurement[2:]
        pointZero = data[:2]
        pointZero = int.from_bytes(pointZero, 'little')
        data = data[2:]
        length = int((len(data)))
        
        values = []
        for i in range(0, length, 2):
            value = int.from_bytes(bytearray([data[i], data[i+1]]), byteOrder)
            values += [float(value)]
        
        print(f'Number of samples: {len(values)}')

        return values            
    
    #Zwraca pomiary po sprawdzeniu nastaw PID
    def checkPID(self, P, I, D):
        self.binaryCommunicator.openSerial()
        print("Checking PID: P:", str(P), "I:", str(I), "D:", str(D))
        message = self.__prepareCheckPID(P, I, D)
        receivedMsg = self.binaryCommunicator.sendData(message)
        
        self.binaryCommunicator.closeSerial()

        if receivedMsg is None:
            print("Check PID status: Error (message has not been received)")
            sys.exit()
    
        print(f'Received measurement data length: {len(receivedMsg)}')
        if len(receivedMsg) == 1:
            print("Check PID status: Error (only 1 byte received)")
            sys.exit()

        if receivedMsg[1] == 0x01:
            print("Check PID status: Ok")
        else:
            print("Check PID status: {} (Invalid message; wait time too short?)".format(receivedMsg.hex(" ", 2)))
            sys.exit()
    
        return self.__prepareMeasurementFromCheckPID(receivedMsg)
    
    def checkSingleParameter(self, U):
        self.binaryCommunicator.openSerial()
        print(f'Checking single parameter: U: {str(U)}')
        message = self.__prepareCheckSingleParameter(U)
        receivedMsg = self.binaryCommunicator.sendData(message)
        
        self.binaryCommunicator.closeSerial()
        print(f'Received measurement data length: {len(receivedMsg)}')

        if len(receivedMsg) == 1:
            print("Check single parameter status: Error (1 byte received)")
            return None 

        if receivedMsg[1] == 0x01:
            print("Check single parameter status: Ok")
        else:
            print("Check single parameter status: {} (Invalid message; wait time too short?)".format(receivedMsg.hex(" ", 2)))
            return None
    
        return self.__prepareMeasurementFromCheckSingleParameter(receivedMsg)