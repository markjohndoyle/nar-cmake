import logging
from os.path import expanduser
import os

__author__ = 'Mark'


class CmakeBuilder:
    # this is the directory where the currently processed CMakeLists.txt is located in
    CMAKE_CURRENT_SOURCE_DIR = "${CMAKE_CURRENT_SOURCE_DIR }"

    def __init__(self, pomParser, projectPath):
        self.log = logging.getLogger("__NAME__")
        self.projectPath = projectPath
        self.m2dir = os.path.join(expanduser("~"), ".m2", "repository")
        self.makeFile = open(os.path.join(self.projectPath,  "CMakeLists.txt"), "w")
        self.groupId = pomParser.groupId
        self.artifactId = pomParser.artifactId
        self.version = pomParser.version
        self.output = pomParser.buildOptions["output"]
        self.cxxFlags = pomParser.buildOptions["compilerFlags"]
        self.srcPath = pomParser.buildOptions["srcPath"]
        self.incPath = pomParser.buildOptions["incPath"]
        self.libPath = os.path.join(self.projectPath, "target", "nar")
        self.testLibPath = os.path.join(self.projectPath,  "target", "test-nar")
        self.dependencies = pomParser.dependencies

        self.target = os.path.join(".", "target")
        # TODO get this from nar config
        self.srcExts = {"c", "cpp"}


    def build(self):
        self.log.info("Generating " + self.makeFile.name)

        self.makeFile.write("make_minimum_required (VERSION 2.6)\n\n")
        self.makeFile.write("project (" + self.groupId + "." + self.artifactId + ")\n")
        self.makeFile.write("\n")

        self.addCxxFlags()
        self.setOutputDir()
        self.addIncludeDir()
        self.addAllSources()
        self.linkDirectories()
        self.addLinkLibs()

        self.addType()


    def addType(self):
        self.makeFile.write("# Targets block\n")
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
        self.makeFile.write("# Source directory block")
        for srcDir in os.listdir(self.srcPath):
            self.makeFile.write("add_subdirectory(" + os.path.join(self.projectPath,  srcDir) + ")\n")
        self.makeFile.write("\n")

    def addIncludeDir(self):
        for incDir in os.listdir(self.incPath):
            self.makeFile.write("include_directories(" + os.path.join(self.projectPath, incDir) + ")\n")
        self.makeFile.write("\n")

    def addAllSources(self):
        self.makeFile.write("# Source file block\n")
        sources = []
        for srcDir in os.listdir(self.srcPath):
            self.makeFile.write("add_subdirectory(" + os.path.join(self.srcPath, srcDir) + ")\n")
            for file in os.listdir(self.srcPath + "/" + srcDir):
                if file.endswith(tuple(self.srcExts)):
                    sources.append(file)

        self.makeFile.write("\nset(SOURCES " + " ".join(sources) + ")\n\n")

    def linkDirectories(self):
        target = self.libPath

    def setOutputDir(self):
        self.makeFile.write("set(CMAKE_CURRENT_BINARY_DIR \"" + os.path.join(self.target, "cmake") + "\")\n")
        self.makeFile.write("\n")

    def addLinkLibs(self):
        self.makeFile.write("# Link libraries block\n")
        for dep in self.dependencies:
            if not dep.foundLocal:
                print("Not a local dependency")
                mvnDep = dep.mvnDep
                # Find in target/nar
                libPath = os.path.join(self.libPath, mvnDep.getFullNarName("gpp"), "lib", mvnDep.getAol("gpp"), mvnDep.libType)
                # TODO move test libs to mvnDependency scope
                testLibPath = os.path.join(self.testLibPath, mvnDep.getFullNarName("gpp"), "lib", mvnDep.getAol("gpp"), mvnDep.libType)
                if os.path.exists(libPath):
                    for file in os.listdir(libPath):
                        if mvnDep.artifactId in file:
                            print("Found lib at " + os.path.join(libPath, file))
                            self.makeFile.write("find_library (" + mvnDep.getFullNarName("gpp").upper() + " " + file + " " + libPath + "\)\n")
                elif os.path.exists(testLibPath):
                    for file in os.listdir(testLibPath):
                        if mvnDep.artifactId in file:
                            print("Found lib at " + os.path.join(libPath, file))
                else:
                    self.log.error("Could not find lib " + mvnDep.getFullNarName())
        self.makeFile.write("\n")




