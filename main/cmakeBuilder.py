import logging
from os.path import expanduser
import os

__author__ = 'Mark'


class CmakeBuilder:
    # this is the directory where the currently processed CMakeLists.txt is located in
    CMAKE_CURRENT_SOURCE_DIR = "${CMAKE_CURRENT_SOURCE_DIR }"

    libsTolink = []

    def __init__(self, pomParser, projectPath):
        self.log = logging.getLogger("__NAME__")
        self.projectPath = projectPath
        self.m2dir = os.path.join(expanduser("~"), ".m2", "repository")
        self.makeFile = open(os.path.join(self.projectPath, "CMakeLists.txt"), "w")
        self.groupId = pomParser.groupId
        self.artifactId = pomParser.artifactId
        self.version = pomParser.version
        self.output = pomParser.buildOptions["output"]
        self.cxxFlags = pomParser.buildOptions["compilerFlags"]
        self.srcPath = pomParser.buildOptions["srcPath"]
        self.incPath = pomParser.buildOptions["incPath"]
        self.libPath = os.path.join(self.projectPath, "target", "nar")
        self.testLibPath = os.path.join(self.projectPath, "target", "test-nar")
        self.dependencies = pomParser.dependencies
        self.headerPostfix = "-noarch"
        self.target = "target"
        # TODO get this from nar config
        self.srcExts = {"c", "cpp" }
        self.binaryName = self.artifactId + "-" + self.version


    def build(self):
        self.log.info("Generating " + self.makeFile.name)

        self.makeFile.write("cmake_minimum_required (VERSION 3.1.3)\n\n")
        self.makeFile.write("project (" + self.binaryName + ")\n")
        self.makeFile.write("\n")

        self.addCxxFlags()
        self.setOutputDir()
        self.addIncludeDirs()
        self.addAllSources()
        self.linkDirectories()
        self.addLinkLibraries()

        self.addBinaryOutput()
        self.linkLibraries()

    def addBinaryOutput(self):
        self.makeFile.write("# Targets block\n")
        if self.output == "executable":
            self.makeFile.write("add_executable(" + self.artifactId + "-" + self.version + " ${SOURCES})\n")
        elif self.output == "shared":
            self.makeFile.write("add_library(" + self.artifactId + "-" + self.version + " SHARED ${SOURCES})\n")
        elif self.output == "static":
            self.makeFile.write("add_library(" + self.artifactId + "-" + self.version + " STATIC ${SOURCES})\n")
        else:
            raise Exception("Unknown output type " + self.output)
        self.makeFile.write("\n")

    def addCxxFlags(self):
        self.makeFile.write("set(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} " + " ".join(self.cxxFlags) + "\")\n")
        self.makeFile.write("\n")

    def addSourceDir(self):
        self.makeFile.write("# Source directory block")
        for srcDir in os.listdir(self.srcPath):
            self.makeFile.write("add_subdirectory(" + os.path.join(self.projectPath, srcDir) + ")\n")
        self.makeFile.write("\n")

    def addIncludeDirs(self):
        # Add project/module include dirs
        for incDir in os.listdir(self.incPath):
            self.makeFile.write("include_directories(" + os.path.join(self.projectPath, incDir) + ")\n")

        # Add dependency includes - This may be local, that is, within the same project hierarchy (another
        # module) or external, that is, brought in by maven to this project's/module's target area.
        for dep in self.dependencies:
            mvnDep = dep.mvnDep
            headerPath = os.path.join(self.libPath, mvnDep.artifactId + "-" + mvnDep.version + self.headerPostfix,
                                      "include")
            if os.path.exists(headerPath):
                self.makeFile.write("include_directories(" + headerPath + ")\n")
        self.makeFile.write("\n")

    def addAllSources(self):
        self.makeFile.write("# Source file block\n")
        sources = []
        for srcDir in os.listdir(self.srcPath):
            self.makeFile.write("add_subdirectory(" + os.path.join(self.srcPath, srcDir) + ")\n")
            for file in os.listdir(self.srcPath + "/" + srcDir):
                if file.endswith(tuple(self.srcExts)):
                    sources.append(file)

        self.makeFile.write("\n")
        self.makeFile.write("set(SOURCES " + " ".join(sources) + ")\n")
        self.makeFile.write("\n")

    def linkDirectories(self):
        target = self.libPath

    def setOutputDir(self):
        self.makeFile.write(
            "set(CMAKE_CURRENT_BINARY_DIR \"${CMAKE_CURRENT_SOURCE_DIR}" + os.path.sep + os.path.join(self.target,
                                                                                                       "cmake") + "\")\n")
        self.makeFile.write("\n")

    def addLinkLibraries(self):
        self.makeFile.write("# Link libraries block\n")
        for dep in self.dependencies:
            if not dep.foundLocal:
                print("Not a local dependency")
                mvnDep = dep.mvnDep
                # Find in target/nar
                libPath = os.path.join(self.libPath, mvnDep.getFullNarName("gpp"), "lib", mvnDep.getAol("gpp"),
                                       mvnDep.libType)
                # TODO move test libs to mvnDependency scope
                testLibPath = os.path.join(self.testLibPath, mvnDep.getFullNarName("gpp"), "lib", mvnDep.getAol("gpp"),
                                           mvnDep.libType)
                if os.path.exists(libPath):
                    for file in os.listdir(libPath):
                        if mvnDep.artifactId in file:
                            libId = os.path.basename(file).rsplit(".", 1)[0].upper()
                            self.libsTolink.append(libId)
                            self.makeFile.write("find_library(" + libId + " " + file + " " + libPath + "\)\n")
                elif os.path.exists(testLibPath):
                    for file in os.listdir(testLibPath):
                        if mvnDep.artifactId in file:
                            print("Found lib at " + os.path.join(libPath, file))
                else:
                    self.log.error("Could not find lib " + mvnDep.getFullNarName())
        self.makeFile.write("\n")

    def linkLibraries(self):
        for libToLink in self.libsTolink:
            self.makeFile.write("target_link_libraries(" + self.binaryName + " " + libToLink + ")")
            self.makeFile.write("\n")





