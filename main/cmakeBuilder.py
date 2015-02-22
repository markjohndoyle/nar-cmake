from main import pomParser

__author__ = 'Mark'

import os

class CmakeBuilder:
    def __init__(self, pomParser):
        self.makeFile = open("CMakeLists.txt", "w")
        self.groupId = pomParser.groupId
        self.artifactId = pomParser.artifactId
        self.version = pomParser.version
        self.output = pomParser.buildOptions["output"]
        self.cxxFlags = pomParser.buildOptions["compilerFlags"]
        self.srcPath = pomParser.buildOptions["srcPath"]
        self.incPath = pomParser.buildOptions["incPath"]


    def build(self):
        self.makeFile.write("make_minimum_required (VERSION 2.6)\n")
        self.makeFile.write("project (" + self.groupId + "." + self.artifactId + ")\n")
        self.makeFile.write("\n")

        self.addType()
        self.addCxxFlags()
        self.addSourceDir()


    def addType(self):
        if self.output == "executable":
            self.makeFile.write("add_executable(" + self.artifactId + "-" + self.version + " ${SOURCES})\n")
        elif self.output == "shared":
            self.makeFile.write("add_library(" + self.artifactId + "-" + self.version + " ${SOURCES})\n")
        elif self.output == "static":
            self.makeFile.write("add_library(" + self.artifactId + "-" + self.version + " ${SOURCES})\n")
        else:
            raise Exception("Unknown output type " + self.output)
        self.makeFile.write("\n")

    def addCxxFlags(self):
        self.makeFile.write("set(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} " + " ".join(self.cxxFlags) + "\")\n")
        self.makeFile.write("\n")

    def addSourceDir(self):
        for srcDir in os.listdir(self.srcPath):
            self.makeFile.write("add_subdirectory(" + self.srcPath + "/" + srcDir + ")\n")



