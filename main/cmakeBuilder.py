__author__ = 'Mark'

from os.path import expanduser
import os


class CmakeBuilder:
    def __init__(self, pomParser):
        self.m2dir = expanduser("~") + "/.m2/repository"
        self.makeFile = open("CMakeLists.txt", "w")
        self.groupId = pomParser.groupId
        self.artifactId = pomParser.artifactId
        self.version = pomParser.version
        self.output = pomParser.buildOptions["output"]
        self.cxxFlags = pomParser.buildOptions["compilerFlags"]
        self.srcPath = pomParser.buildOptions["srcPath"]
        self.incPath = pomParser.buildOptions["incPath"]
        self.libPath = pomParser.projectRoot + "/target/nar"
        self.testLibPath = pomParser.projectRoot + "/target/test-nar"
        self.target = "./target/cmake"

        # TODO get this from nar config
        self.srcExts = {"c", "cpp"}


    def build(self):
        self.makeFile.write("make_minimum_required (VERSION 2.6)\n\n")
        self.makeFile.write("project (" + self.groupId + "." + self.artifactId + ")\n")
        self.makeFile.write("\n")

        self.addCxxFlags()
        self.addIncludeDir()
        self.addAllSources()
        self.addType()
        self.linkDirectories()
        self.setOutputDir()
        # self.addSourceDir()


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

    def addIncludeDir(self):
        for incDir in os.listdir(self.incPath):
            self.makeFile.write("include_directories(" + incDir + ")\n")
        self.makeFile.write("\n")

    def addAllSources(self):
        sources = []
        for srcDir in os.listdir(self.srcPath):
            for file in os.listdir(self.srcPath + "/" + srcDir):
                if file.endswith(tuple(self.srcExts)):
                    sources.append(file)

        self.makeFile.write("set(SOURCES " + " ".join(sources) + ")\n\n")

    def linkDirectories(self):
        target = self.libPath

    def setOutputDir(self):
        self.makeFile.write("set(CMAKE_RUNTIME_OUTPUT_DIRECTORY " + self.target + ")\n")




