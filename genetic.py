#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 25 18:37:02 2021

@author: krzysztof
"""

import json
import geneticUtils
import copy

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
            self.actualState["parameters"] = parameters
            self.actualState["content"] = dict()
            self.actualState["content"]["actualPopulation"] = dict()
            self.actualState["content"]["oldPopulations"] = list()
            self.actualState["content"]["actualPopulation"]["generation"] = 0
            geneticUtils.saveState("./savedState.json", self.actualState)

    def __checkIndividualPID(self, individual):
        # Load pattern
        patternFile = open("./pattern.json")
        pattern = json.load(patternFile)
        self.vibrationUnit.loadPattern(pattern)

        P, I, D = individual

        # Check PID
        measurement = self.vibrationUnit.checkPID(P, I, D)

        mean = float(sum(measurement) / len(measurement))
        for i in range(0, len(measurement)):
            measurement[i] = measurement[i] - mean

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
            bestIndividual = self.__geneticExecutor()

        print("Best individual:")
        info = "P: {P} I: {I} D: {D}".format(
            P=bestIndividual["P"], I=bestIndividual["I"], D=bestIndividual["D"])
        print(info)
        info = "Regulation time: {time}".format(
            time=bestIndividual["regulationTimeMs"])
        print(info)

        return {"P": bestIndividual["P"], "I": bestIndividual["I"], "D": bestIndividual["D"]}
