#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 25 18:01:23 2021

@author: krzysztof
"""

import struct

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
        print("Loading pattern...")
        message = self.__prepareLoadingPatternMsg(pattern)
        
        receivedMsg = self.binaryCommunicator.sendData(message)
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
        
        return values
                
    
    #Zwraca pomiary po sprawdzeniu nastaw PID
    def checkPID(self, P, I, D):
        self.binaryCommunicator.openSerial()
        print("Checking PID: P:", str(P), "I:", str(I), "D:", str(D))
        message = self.__prepareCheckPID(P, I, D)
        receivedMsg = self.binaryCommunicator.sendData(message)
        
        self.binaryCommunicator.closeSerial()
        
        if receivedMsg[1] == 0x01:
            print("Check PID status: Ok")
        else:
            print("Check PID status: Error")
            return None
    
        return self.__prepareMeasurementFromCheckPID(receivedMsg)