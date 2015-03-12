import logging
from os.path import expanduser
import os

__author__ = 'Mark'


class CmakeBuilder:
    # this is the directory where the currently processed CMakeLists.txt is located in
    CMAKE_CURRENT_SOURCE_DIR = "${CMAKE_CURRENT_SOURCE_DIR }"

    libsTolink = []

    def __init__(self, pomParser, projectPath):
        self.parser = pomParser
        self.log = logging.getLogger("__NAME__")
        self.projectPath = projectPath
        self.m2dir = os.path.join(expanduser("~"), ".m2", "repository")
        self.makeFile = open(os.path.join(self.projectPath, "CMakeLists.txt"), "w")
        self.groupId = pomParser.groupId
        self.artifactId = pomParser.artifactId
        self.version = pomParser.version
        self.output = pomParser.buildOptions["output"]
        self.cxxFlags = pomParser.buildOptions["compilerFlags"]
        self.libPath = os.path.join(self.projectPath, "target", "nar")
        self.testLibPath = os.path.join(self.projectPath, "target", "test-nar")
        self.dependencies = pomParser.dependencies
        self.headerPostfix = "-noarch"
        self.target = "target"
        # TODO get this from nar config
        self.srcExts = {"c", "cpp"}
        self.binaryName = self.artifactId + "-" + self.version
        self.cmakeTarget = os.path.join(self.target, "cmake")


    def build(self):
        self.log.info("Generating " + self.makeFile.name)

        self.makeFile.write("cmake_minimum_required (VERSION 3.1.3)\n\n")
        self.makeFile.write("project (" + self.binaryName + ")\n")
        self.makeFile.write("\n")

        self.addCxxFlags()
        # self.setOutputDir()
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
        incPath = self.parser.buildOptions["incPath"]
        for incDir in os.listdir(incPath):
            self.makeFile.write("include_directories(" + os.path.join(incPath, incDir) + ")\n")

        # Add dependency includes - This may be local, that is, within the same project hierarchy (another
        # module) or external, that is, brought in by maven to this project's/module's target area.
        for dep in self.dependencies.values():
            # mvnDep = dep.mvnDep
            if dep.foundLocal:
                headerPath = os.path.join(self.parser.localModules[dep.groupId + "." + dep.artifactId], "src",
                                          "main", "include")
            else:
                headerPath = os.path.join(self.libPath, dep.artifactId + "-" + dep.version + self.headerPostfix,
                                          "include")
            if os.path.exists(headerPath):
                self.makeFile.write("include_directories(" + headerPath + ")\n")
            else:
                self.log.error("header path " + headerPath + " does not exist. Currently not supporting test includes.")
        self.makeFile.write("\n")

    def addAllSources(self):
        self.makeFile.write("# Source file block\n")
        srcPath = self.parser.buildOptions["srcPath"]
        sources = []
        for srcDir in os.listdir(os.path.join(self.projectPath, srcPath)):
            # self.makeFile.write("add_subdirectory(" + os.path.join(srcPath, srcDir) + ")\n")
            subSrcPath = os.path.join(self.projectPath, srcPath, srcDir)
            for file in os.listdir(subSrcPath):
                if file.endswith(tuple(self.srcExts)):
                    sources.append(os.path.join(srcPath, srcDir, file))

        self.makeFile.write("\n")
        self.makeFile.write("set(SOURCES \n\t" + "\n\t".join(sources) + ")\n")
        self.makeFile.write("\n")

    def linkDirectories(self):
        target = self.libPath

    def setOutputDir(self):
        self.makeFile.write(
            "set(CMAKE_CURRENT_BINARY_DIR \"${CMAKE_CURRENT_SOURCE_DIR}" + os.path.sep + self.cmakeTarget + "\")\n")
        self.makeFile.write("\n")

    # Currently no checks are carried otu for header only libs so there may be superfluous find_library entries
    def addLinkLibraries(self):
        self.makeFile.write("# Link libraries block\n")
        for dep in self.dependencies.values():
            if dep.scope is not "compile":
                self.log.warn("Only supporting compile scope. " +dep.getFullNarName() + " is " + dep.scope)
                continue

            if not dep.foundLocal:
                # Find in target/nar
                libPath = os.path.join(self.libPath, dep.getFullNarName("gpp"), "lib", dep.getAol("gpp"), dep.libType)
            else:
                libPath = os.path.join(dep.path, self.cmakeTarget)

            libId = dep.artifactId.upper()
            self.makeFile.write("find_library(" + libId + " " + dep.artifactId + " HINTS " + libPath + "\)\n")
            self.libsTolink.append(libId)
        self.makeFile.write("\n")


    def linkLibraries(self):
        for libToLink in self.libsTolink:
            self.makeFile.write("target_link_libraries(" + self.binaryName + " " + libToLink + ")")
            self.makeFile.write("\n")





