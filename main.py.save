#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 25 17:57:55 2021

@author: krzysztof
"""

from serial import Serial
from binarycommunicator import BinaryCommunicator
from vibration import VibrationUnit
from genetic import GeneticsPID

# Parametry dla algorytmu genetycznego w postaci słownika
# populationCount - rozmiar populacji
# maxGeneration - maksymalna ilość generacji

# Warunek końca spełni się kiedy czas regulacji nie zmieni się przez x generacji
# noChangeGenerations - ilość generacji do spełnienia warunku końca

# W przypadku algorytmu genetycznego dla PID:
# maxP - maksymalna wartość P
# minP - minimalna wartość P
# maxI - maksymalna wartość I
# minI - minimalna wartość I
# maxD - maksymalna wartość D
# minD - minimalna wartość D


geneticParameters = dict()
geneticParameters["populationCount"] = 25
geneticParameters["maxGeneration"] = 25
geneticParameters["noChangeGenerations"] = 25
# Metoda selekcji rodziców
geneticParameters["parentSelectionMetod"] = "tournament"
# Określa rozmiary turnieju (Nie może być większa niż rozmiar populacji)
# Im większa wartość parametru, tym większy napór selekcyjny
geneticParameters["tournamentSize"] = 2
# Przekształcanie postaci funkcji celu
# Stała dla obliczania przystosowania poprzez przekształcenie z problemu minimum w problem maksimum
geneticParameters["maxTimeMsForAdaptCalc"] = 7000

geneticParameters["crossoverProbability"] = 0.8
geneticParameters["mutationProbability"] = 0.1

# Parametr Pe dla krzyżowania równomiernego
geneticParameters["Pe"] = 0.5

# Metoda krzyżowania:
# Uniform - równomierne
# Arithmetical - arytmetyczne
# Domyślnie jest arytmetyczne
geneticParameters["CrossoverMethod"] = "Arithmetical"

geneticParameters["maxP"] = 5.0
geneticParameters["minP"] = -5.0
geneticParameters["maxI"] = 5.0
geneticParameters["minI"] = -5.0
geneticParameters["maxD"] = 5.0
geneticParameters["minD"] = -5.0

serialDevice = Serial("/dev/ttyACM0", baudrate=921600, timeout=120)
serialBinary = BinaryCommunicator(serialDevice)
vibrationUnit = VibrationUnit(serialBinary)

geneticUnit = GeneticsPID(vibrationUnit, geneticParameters)


# Result is the best resolve tuple {P, I, D}
bestIndividual = geneticUnit.execGeneticsPID()
