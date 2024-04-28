#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 25 18:37:02 2021

@author: krzysztof
"""

import json
import geneticUtils
import copy
import random
import csv
import os
import numpy as np
from calculations import parse_measurements

# Other consts
# Use to discard zero values
epsilon = 10.0


class GeneticsPID():
    def __init__(self, vibrationDevice, parameters):
        self.vibrationUnit = vibrationDevice

        self.actualState = geneticUtils.loadState("./savedState.json")

        if self.actualState == None:
            self.actualState = dict()
            self.actualState["finished"] = False
            self.actualState["finishedDataSpace"] = False
            self.actualState["dataSpaceIteration"] = -1
            self.actualState["parameters"] = parameters
            self.actualState["content"] = dict()
            self.actualState["content"]["actualPopulation"] = dict()
            self.actualState["content"]["oldPopulations"] = list()
            self.actualState["content"]["zerothDataSpace"] = list()
            self.actualState["content"]["actualPopulation"]["generation"] = 0
            geneticUtils.saveState("./savedState.json", self.actualState)

    def __checkIndividualPID(self, individual):
        # Load pattern
        patternFile = open("./pattern.json")
        pattern = json.load(patternFile)
        self.vibrationUnit.loadPattern(pattern)

        P, I, D = individual

        # Check PID
        measurement, u = self.vibrationUnit.checkPID(P, I, D)
        mean = float(sum(measurement) / len(measurement))
        for i in range(0, len(measurement)):
            measurement[i] = measurement[i] - mean

        regulationTime = geneticUtils.calculateRegulationTime(measurement)
        print(f'Regulation time: {regulationTime} ms')
        x, v, a = parse_measurements(measurement, u, 
                                     skipped_samples=0, show_plot=False)

        return measurement

    def __checkPopulation(self, population):

        checkedPopulation = []
        for individual in population["population"]:
            if individual["regulationTimeMs"] != None:
                checkedPopulation += [individual]
                continue

            P = individual["P"]
            I = individual["I"]
            D = individual["D"]
            measurement = self.__checkIndividualPID((P, I, D))
            regulationTime = geneticUtils.calculateRegulationTime(measurement)
            print(f'Regulation time: {regulationTime} ms')

            individual["regulationTimeMs"] = regulationTime
            checkedPopulation += [individual]

        population["population"] = checkedPopulation
        bestIndividual = geneticUtils.findBestIndividualPerRegulationTime(
            population)
        population["bestRegulationTimeMs"] = bestIndividual["regulationTimeMs"]

        lastBestRegulation = geneticUtils.findLastBestRegulationTimeMs(
            self.actualState["content"]["oldPopulations"], population["generation"])

        if lastBestRegulation["bestRegulationTimeMs"] == population["bestRegulationTimeMs"]:
            population["noChangeGenerations"] = lastBestRegulation["noChangeGenerations"]
            population["noChangeGenerations"] += 1
        else:
            population["noChangeGenerations"] = 0

        return population

    def __checkEndCondition(self):
        paramNoChangeGenerations = self.actualState["parameters"]["noChangeGenerations"]
        paramMaxGeneration = self.actualState["parameters"]["maxGeneration"]
        endCondition = self.actualState["content"]["actualPopulation"]["noChangeGenerations"] \
            >= paramNoChangeGenerations

        generationCheck = self.actualState["content"]["actualPopulation"]["generation"] \
            >= paramMaxGeneration

        endCondition = endCondition or generationCheck

        return endCondition

    def __selectParents(self, population):
        selectionMethod = geneticUtils.getParentSelectionMethod(
            self.actualState["parameters"]["parentSelectionMetod"])

        if self.actualState["parameters"]["parentSelectionMetod"] == "tournament":
            parents = selectionMethod(
                population, self.actualState["parameters"]["tournamentSize"])
        else:
            parents = selectionMethod(population)

        return parents

    def __geneticOperators(self, population, actualGeneration):

        crossoverProbability = self.actualState["parameters"]["crossoverProbability"]
        mutationProbability = self.actualState["parameters"]["mutationProbability"]

        # Crossover
        parentsCopy = copy.deepcopy(population)
        children = geneticUtils.crossover(
            parentsCopy, crossoverProbability, self.actualState["parameters"])

        # Mutation
        children = geneticUtils.nonUniformMutation(
            children, mutationProbability, self.actualState["parameters"], actualGeneration, self.actualState["parameters"]["maxGeneration"])

        return children

    def __createNewPopulation(self, children):

        newPopulation = []
        newPopulation += children
        self.actualState["content"]["actualPopulation"]["population"] = newPopulation
        self.actualState["content"]["actualPopulation"]["generation"] += 1
        self.actualState["content"]["actualPopulation"]["bestRegulationTimeMs"] = None

    def __geneticExecutor(self):

        while True:

            actualPopulation = self.actualState["content"]["actualPopulation"]

            # Check popultation
            actualPopulation = self.__checkPopulation(actualPopulation)

            # Stop if stop condition is true
            if self.__checkEndCondition() == True:
                print("Genetic algorithm finished")
                self.actualState["content"]["actualPopulation"] = actualPopulation
                self.actualState["finished"] = True
                geneticUtils.saveState("./savedState.json", self.actualState)
                return geneticUtils.findBestIndividualPerRegulationTime(actualPopulation)

            # Parents selection
            parents = self.__selectParents(actualPopulation)

            # Genetic operations
            newPopulation = self.__geneticOperators(
                parents, actualPopulation["generation"])

            self.actualState["content"]["oldPopulations"] += [
                copy.deepcopy(actualPopulation)]

            # Create new population
            # Copy best individual to new generation
            # bestIndividual = geneticUtils.findBestIndividualPerRegulationTime(actualPopulation)
            self.__createNewPopulation(newPopulation)

            # Save state to file
            geneticUtils.saveState("./savedState.json", self.actualState)

    def execGeneticsPID(self):

        if self.actualState["content"]["actualPopulation"]["generation"] == 0:
            # population = geneticUtils.generateStartupPopulationPID(self.actualState["parameters"])
            population = geneticUtils.createDefaultStartupPopulationPID()
            self.actualState["content"]["actualPopulation"]["generation"] = 1
            self.actualState["content"]["actualPopulation"]["noChangeGenerations"] = 0
            self.actualState["content"]["actualPopulation"]["bestRegulationTimeMs"] = None
            self.actualState["content"]["actualPopulation"]["population"] = population
            geneticUtils.saveState("./savedState.json", self.actualState)

        if self.actualState["finished"] == True:
            print("Genetic algorithm is finished")
            actualPopulation = self.actualState["content"]["actualPopulation"]
            bestIndividual = geneticUtils.findBestIndividualPerRegulationTime(
                actualPopulation)
        else:
            hasInitializedDataSpace = len(self.actualState["content"]["zerothDataSpace"]) == 0
            hasFinishedDataSpace = self.actualState["finishedDataSpace"]

            if hasInitializedDataSpace:
                with open("dataSpacePID.csv", 'a', newline='') as file_csv:
                    writer = csv.writer(file_csv)
                    writer.writerow(["index", "P", "I", "D", "x", "v", "a", "regulation_time"])

            configFile = open("./config.json")
            config = json.load(configFile)
            if config["start_genetics_first"]:
                bestIndividual = self.__geneticExecutor()
                if not hasInitializedDataSpace or not hasFinishedDataSpace:
                    self.generateDataSpace()
            else:
                if not hasInitializedDataSpace or not hasFinishedDataSpace:
                    self.generateDataSpace()
                bestIndividual = self.__geneticExecutor()

                

        print("Best individual:")
        info = "P: {P} I: {I} D: {D}".format(
            P=bestIndividual["P"], I=bestIndividual["I"], D=bestIndividual["D"])
        print(info)
        info = "Regulation time: {time}".format(
            time=bestIndividual["regulationTimeMs"])
        print(info)

        return {"P": bestIndividual["P"], "I": bestIndividual["I"], "D": bestIndividual["D"]}

    def generateDataSpace(self):

        random.seed()
        lenIterations = 1000
        iterationsDone = self.actualState["dataSpaceIteration"] + 1
        for i in range(iterationsDone, lenIterations):
            # Load pattern
            patternFile = open("./pattern.json")
            pattern = json.load(patternFile)
            self.vibrationUnit.loadPattern(pattern)

            configFile = open("./config.json")
            config = json.load(configFile)
            random_pid = config["random_pid"]
            show_plots = config["show_plots"]
            n_skip = config["n_skip"]

            if random_pid:
                P = random.uniform(config["P"][0], config["P"][1])
                I = random.uniform(config["I"][0], config["I"][1])
                D = random.uniform(config["D"][0], config["D"][1])
            else:
                P = config["hard_pid"][0]
                I = config["hard_pid"][1]
                D = config["hard_pid"][2]

            # Check PID
            measurements, pidResponses = self.vibrationUnit.checkPID(P, I, D)

            mean = float(sum(measurements[n_skip:]) / len(measurements[n_skip:]))
            for j in range(0, len(measurements)):
                measurements[j] = measurements[j] - mean

            start_index = np.asarray(measurements).argmax()
            if (start_index > 100):
                start_index = 0

            regulationTime = geneticUtils.calculateRegulationTime(measurements[start_index:])
            
            if (regulationTime > 5000):
                regulationTime = -1
                print(f'Regulation time: {regulationTime} ms (system is not stable)')
            else:
                print(f'Regulation time: {regulationTime} ms')

            x, v, a = parse_measurements(measurements, pidResponses, 
                                         skipped_samples=start_index, show_plot=show_plots)

            content = self.actualState["content"]["zerothDataSpace"]
            population = dict()
            population["number"] = i
            population["P"] = P
            population["I"] = I
            population["D"] = D
            population["max_x"] = x
            population["max_v"] = v
            population["max_a"] = a
            population["regulationTimeMs"] = regulationTime
            content.append(population)
            self.actualState["dataSpaceIteration"] = i
            geneticUtils.saveState("./savedState.json", self.actualState)

            with open("dataSpacePID.csv", 'a', newline='') as file_csv:
                writer = csv.writer(file_csv)
                writer.writerow([i, P, I, D, x, v, a, regulationTime])

            if not os.path.exists("time_series/"):
                os.makedirs("time_series/")
            with open(f"time_series/{i}.csv", 'x', newline='') as file_csv:
                writer = csv.writer(file_csv)
                writer.writerow(["index", "x", "u"])
                for j in range(len(measurements)):
                    writer.writerow([j, measurements[j], pidResponses[j]])

        self.actualState["finishedZerothDataSpace"] = True
        geneticUtils.saveState("./savedState.json", self.actualState)


