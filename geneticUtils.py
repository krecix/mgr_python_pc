#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 25 18:49:39 2021

@author: krzysztof
"""

import numpy as np
from scipy.signal import hilbert
from random import SystemRandom
import json
import copy

MOVE_FILTER_LENGTH = 200
REGULATION_TIME_PERCENTAGE = 0.30

cryptogen = SystemRandom()
#

def loadState(file):
    try:
        file = open(file, "r")
        return json.load(file)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def saveState(file, state):
    outFile = open(file, "w")
    json.dump(state, outFile, indent=4)

# Obliczanie obwiedni sygnału


def getSignalEnvelope(signal):
    envelope = hilbert(signal)
    # -2 -> usunięcie dwóch ostatnich próbek które dziwnie wyskoczyły w górę
    return np.abs(envelope)[:-2]


def movingFilter(signalIn, filterLength):
    signal = signalIn.copy()
    # Tymczasowa zmienna która przechowuje wartość w ostatnio sumowanym punkcie
    lastValue = 0

    # Suma dla zerowej próbki
    sumValue = signal[0]
    lastValue = sumValue
    for i in range(1, min(filterLength, len(signal))):
        sumValue += signal[i]

    signal[0] = sumValue / filterLength

    # Suma dla reszty próbek
    i = 1
    while i < (len(signal) - filterLength):
        sumValue -= lastValue
        sumValue += signal[i+filterLength-1]
        sumDiv10 = sumValue / filterLength
        signal[i] = sumDiv10
        i += 1
        lastValue = sumDiv10

    signal = signal[:len(signal)-filterLength]

    return signal


def calculateMean(population):
    population = population["population"]

    populationCount = len(population)

    sumValue = 0

    for individual in population:
        sumValue += individual["regulationTimeMs"]

    return sumValue / populationCount


def calculateStandardDeviation(population):
    mean = calculateMean(population)
    population = population["population"]

    populationCount = len(population)

    variance = 0
    for individual in population:
        variance += (individual["regulationTimeMs"] - mean)**2
    variance = variance / populationCount

    return np.sqrt(variance)

# Funkcja przystosowania to czas regulacji
# Im krótszy czas regulacji, tym układ jest lepszy
# Czas regulacji obliczamy poprzez sprawdzenie
# w ile czasu amplituda (wartość obwiedni Hilberta)
# spadnie poniżesz 0.05 wartości maksymalnej


def calculateRegulationTime(measurement):

    envelope = getSignalEnvelope(measurement)
    filteringEnvelope = movingFilter(envelope, MOVE_FILTER_LENGTH)
    maxValueIndex = filteringEnvelope.argmax()
    maxValue = filteringEnvelope[maxValueIndex]

    index = maxValueIndex
    amplitude = maxValue

    while (index < len(filteringEnvelope)) and (amplitude > (maxValue*REGULATION_TIME_PERCENTAGE)):
        amplitude = filteringEnvelope[index]
        index += 1

    if amplitude > (maxValue*REGULATION_TIME_PERCENTAGE):
        # No regulation
        return len(filteringEnvelope)

    index -= 1

    return int(index - maxValueIndex)


def generateStartupPopulationPID(geneticParameters):
    population = []
    populationCount = geneticParameters["populationCount"]
    for i in range(0, populationCount):
        individual = dict()
        individual["P"] = cryptogen.uniform(
            geneticParameters["minP"], geneticParameters["maxP"])
        individual["I"] = cryptogen.uniform(
            geneticParameters["minI"], geneticParameters["maxI"])
        individual["D"] = cryptogen.uniform(
            geneticParameters["minD"], geneticParameters["maxD"])
        individual["regulationTimeMs"] = None
        population += [individual]
    return population


def createTournamentGroup(population, tournamentSize):
    tournamentGroup = []
    populationCount = len(population["population"])

    populationTemp = copy.deepcopy(population)

    for _ in range(0, tournamentSize):
        if populationCount < 2:
            individual = populationTemp["population"][0]
            drawingIndex = 0
        else:
            drawingIndex = cryptogen.randrange(0, populationCount, 1)
            individual = populationTemp["population"][drawingIndex]
        populationTemp["population"].pop(drawingIndex)
        populationCount -= 1
        tournamentGroup += [individual]

    return tournamentGroup


def findBestIndividualPerRegulationTime(population):
    best = population["population"][0]
    bestRegulationTime = population["population"][0]["regulationTimeMs"]

    for individual in population["population"]:
        if individual["regulationTimeMs"] < bestRegulationTime:
            best = individual
            bestRegulationTime = individual["regulationTimeMs"]

    return best


def findLastBestRegulationTimeMs(oldPopulations, actualGeneration):

    if len(oldPopulations) == 0:
        return {"bestRegulationTimeMs": 0, "noChangeGenerations": 0}

    for population in oldPopulations:
        if population["generation"] == (actualGeneration - 1):
            return {"bestRegulationTimeMs": population["bestRegulationTimeMs"], "noChangeGenerations": population["noChangeGenerations"]}

    return {"bestRegulationTimeMs": 0, "noChangeGenerations": 0}


def tournamentSelectionMetod(population, tournamentSize):
    parents = []
    populationCount = len(population["population"])

    for _ in range(0, populationCount):
        tournamentGroup = {"population": createTournamentGroup(
            population, tournamentSize)}
        bestIndividual = findBestIndividualPerRegulationTime(tournamentGroup)
        parents += [bestIndividual]

    return parents


def getParentSelectionMethod(methodName):
    return {
        'tournament': tournamentSelectionMetod,
    }.get(methodName, "tournament")


def isSameIndividuals(couple):
    (couple1, couple2) = couple

    same = True

    if couple1["P"] != couple2["P"]:
        same = False
        return same
    if couple1["I"] != couple2["I"]:
        same = False
        return same
    if couple1["D"] != couple2["D"]:
        same = False
        return same

    return same


def arithmeticalCrossCouple(couple, crossoverProbability):

    if isSameIndividuals(couple):
        return couple

    drawingValue = cryptogen.uniform(0, 1)
    if drawingValue >= crossoverProbability:
        return (couple[0], couple[1])
    else:
        k = cryptogen.uniform(0, 1)
        child1 = dict()
        child1["P"] = couple[0]["P"] + (k*(couple[1]["P"] - couple[0]["P"]))
        child1["I"] = couple[0]["I"] + (k*(couple[1]["I"] - couple[0]["I"]))
        child1["D"] = couple[0]["D"] + (k*(couple[1]["D"] - couple[0]["D"]))
        child1["regulationTimeMs"] = None
        child2 = dict()
        child2["P"] = couple[1]["P"] + couple[0]["P"] - child1["P"]
        child2["I"] = couple[1]["I"] + couple[0]["I"] - child1["I"]
        child2["D"] = couple[1]["D"] + couple[0]["D"] - child1["D"]
        child2["regulationTimeMs"] = None

        return (child1, child2)


def arithmeticalCrossover(parents, crossoverProbability):

    parentsCount = len(parents)
    coupleCount = int(parentsCount / 2)
    individualWithoutCouple = parentsCount - (coupleCount * 2)

    # Generate couples
    couples = []
    actualSize = coupleCount * 2
    for _ in range(0, coupleCount):
        drawingIndex = cryptogen.randrange(0, actualSize, 1)
        individual1 = parents[drawingIndex]
        parents.pop(drawingIndex)
        actualSize -= 1
        drawingIndex = cryptogen.randrange(0, actualSize, 1)
        individual2 = parents[drawingIndex]
        parents.pop(drawingIndex)
        actualSize -= 1
        couples += [[individual1, individual2]]

    children = []
    for couple in couples:
        child1, child2 = arithmeticalCrossCouple(couple, crossoverProbability)
        children += [child1, child2]

    if individualWithoutCouple > 0:
        children += [parents[0]]
        parents.pop(0)

    return children


def uniformCrossCouple(couple, crossoverProbability, PeParameter):
    if isSameIndividuals(couple):
        return couple

    drawingValue = cryptogen.uniform(0, 1)
    if drawingValue >= crossoverProbability:
        return (couple[0], couple[1])
    else:
        child1 = dict()
        child2 = dict()
        randomNum = cryptogen.uniform(0, 1)
        if randomNum < PeParameter:
            child1["P"] = couple[0]["P"]
            child2["P"] = couple[1]["P"]
        else:
            child1["P"] = couple[1]["P"]
            child2["P"] = couple[0]["P"]

        randomNum = cryptogen.uniform(0, 1)
        if randomNum < PeParameter:
            child1["I"] = couple[0]["I"]
            child2["I"] = couple[1]["I"]
        else:
            child1["I"] = couple[1]["I"]
            child2["I"] = couple[0]["I"]

        randomNum = cryptogen.uniform(0, 1)
        if randomNum < PeParameter:
            child1["D"] = couple[0]["D"]
            child2["D"] = couple[1]["D"]
        else:
            child1["D"] = couple[1]["D"]
            child2["D"] = couple[0]["D"]

        child1["regulationTimeMs"] = None
        child2["regulationTimeMs"] = None

        return (child1, child2)


def uniformCrossover(parents, crossoverProbability, PeParameter):
    parentsCount = len(parents)
    coupleCount = int(parentsCount / 2)
    individualWithoutCouple = parentsCount - (coupleCount * 2)

    # Generate couples
    couples = []
    actualSize = coupleCount * 2
    for _ in range(0, coupleCount):
        drawingIndex = cryptogen.randrange(0, actualSize, 1)
        individual1 = parents[drawingIndex]
        parents.pop(drawingIndex)
        actualSize -= 1
        drawingIndex = cryptogen.randrange(0, actualSize, 1)
        individual2 = parents[drawingIndex]
        parents.pop(drawingIndex)
        actualSize -= 1
        couples += [[individual1, individual2]]

    children = []
    for couple in couples:
        child1, child2 = uniformCrossCouple(
            couple, crossoverProbability, PeParameter)
        children += [child1, child2]

    if individualWithoutCouple > 0:
        children += [parents[0]]
        parents.pop(0)

    return children


def crossover(parents, crossoverProbability, parameters):

    if parameters["CrossoverMethod"] == 'Uniform':
        return uniformCrossover(parents, crossoverProbability, parameters["Pe"])
    else:  # Arithmetical
        return arithmeticalCrossover(parents, crossoverProbability)


def mutateNonUniformChild(child, geneticParameters, a, actualGeneration, maxGeneration):
    mutatedChild = dict()
    if a < 0.5:
        mutatedChild["P"] = child["P"] + a*(geneticParameters["maxP"] - child["P"])*(
            1.0 - (actualGeneration/maxGeneration))**2
        mutatedChild["I"] = child["I"] + a*(geneticParameters["maxI"] - child["I"])*(
            1.0 - (actualGeneration/maxGeneration))**2
        mutatedChild["D"] = child["D"] + a*(geneticParameters["maxD"] - child["D"])*(
            1.0 - (actualGeneration/maxGeneration))**2
    else:
        mutatedChild["P"] = child["P"] - a*(child["P"] - (geneticParameters["minP"]))*(
            1.0 - (actualGeneration/maxGeneration))**2
        mutatedChild["I"] = child["I"] - a*(child["I"] - (geneticParameters["minI"]))*(
            1.0 - (actualGeneration/maxGeneration))**2
        mutatedChild["D"] = child["D"] - a*(child["D"] - (geneticParameters["minD"]))*(
            1.0 - (actualGeneration/maxGeneration))**2
    mutatedChild["regulationTimeMs"] = None

    return mutatedChild


def nonUniformMutation(children, mutationProbability, geneticParameters, actualGeneration, maxGeneration):

    mutatedChildren = []
    for child in children:
        drawingValue = cryptogen.uniform(0, 1)
        if drawingValue >= mutationProbability:
            mutatedChildren += [child]
        else:
            a = cryptogen.uniform(0, 1)
            mutatedChildren += [mutateNonUniformChild(
                child, geneticParameters, a, actualGeneration, maxGeneration)]

    return mutatedChildren


def createDefaultStartupPopulationPID():
    population = []

    individual = dict()
    individual["P"] = 2.213
    individual["I"] = 0.921
    individual["D"] = 4.867
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 1.213
    individual["I"] = -3.521
    individual["D"] = -2.052
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 1.823
    individual["I"] = -1.963
    individual["D"] = 2.111
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 1.653
    individual["I"] = -3.111
    individual["D"] = 0.237
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 0.551
    individual["I"] = 0.288
    individual["D"] = -4.323
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 1.217
    individual["I"] = -0.728
    individual["D"] = -0.023
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 0.924
    individual["I"] = 0.618
    individual["D"] = 0.323
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 4.024
    individual["I"] = 4.111
    individual["D"] = 4.021
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 3.524
    individual["I"] = -3.611
    individual["D"] = -3.191
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 2.025
    individual["I"] = 2.988
    individual["D"] = 2.001
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 0.011
    individual["I"] = 3.582
    individual["D"] = 1.027
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 2.014
    individual["I"] = -4.761
    individual["D"] = 1.636
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 3.083
    individual["I"] = -0.237
    individual["D"] = 3.561
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 2.908
    individual["I"] = 1.582
    individual["D"] = 0.707
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 0.097
    individual["I"] = 2.824
    individual["D"] = 3.773
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 4.908
    individual["I"] = 1.582
    individual["D"] = 0.707
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = -2.703
    individual["I"] = 1.582
    individual["D"] = -1.868
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 1.856
    individual["I"] = 1.958
    individual["D"] = -0.707
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = -1.856
    individual["I"] = 1.958
    individual["D"] = 3.284
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 1.419
    individual["I"] = 1.582
    individual["D"] = 1.515
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = -3.323
    individual["I"] = 0.794
    individual["D"] = -0.423
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 3.354
    individual["I"] = -0.686
    individual["D"] = -1.981
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = 2.189
    individual["I"] = -2.478
    individual["D"] = 1.097
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = -2.680
    individual["I"] = 2.305
    individual["D"] = 0.831
    individual["regulationTimeMs"] = None
    population += [individual]

    individual = dict()
    individual["P"] = -3.102
    individual["I"] = 1.558
    individual["D"] = 0.179
    individual["regulationTimeMs"] = None
    population += [individual]

    return population
