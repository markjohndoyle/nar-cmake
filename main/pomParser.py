# import xml.etree.cElementTree as ETree
import xml.etree.cElementTree as ETree
from builtins import print
import os

from main import mavenDependency as mvnDep


__author__ = 'Mark'

# Parses nar module poms


class PomParser:
    NAR_PLUG = "nar-maven-plugin"
    ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
    parentPathDefault = "../"

    narModule = False
    dependencies = []
    buildOptions = {"compiler": "g++",
                    "linker": "g++",
                    "debug": True,
                    "compilerFlags": {"-std=c++11"},
                    "sysLibs": set(),
                    "output": "executable"}



    # Parses the pom pulling out nar specifics.
    def parsePom(self, filepath):
        print("Parsing pom " + filepath)

        tree = ETree.parse(filepath)
        project = tree.getroot()

        parent = self.getParent(project)
        if parent:
            print("Has parent")
            parentFile = self.findParentFile(parent, filepath)

        plugins = project.findall("mvn:build/mvn:pluginManagement/mvn:plugins/mvn:plugin", self.ns)
        self.gatherNarPluginConfig(plugins)
        plugins = project.findall("mvn:build/mvn:plugins/mvn:plugin", self.ns)
        self.gatherNarPluginConfig(plugins)

        dependencies = project.findall("mvn:dependencies/mvn:dependency", self.ns)
        self.gatherDependencies(dependencies)

        print(self.buildOptions)
        for dep in self.dependencies:
            print(dep.getAol("gpp"))

    # Checks if there is a nar plugin definition in the pom
    def gatherNarPluginConfig(self, pluginsNode):
        for plugin in pluginsNode:
            artifactId = plugin.find("mvn:artifactId", self.ns)
            if artifactId.text == self.NAR_PLUG:
                print("We have a nar plugin")
                sysLibsNode = plugin.findall("mvn:configuration/mvn:linker/mvn:sysLibs/mvn:sysLib/mvn:name", self.ns)
                sysLibs = self.buildOptions["sysLibs"]
                for sysLib in sysLibsNode:
                    sysLibs.add(sysLib.text)
                self.buildOptions["sysLibs"] = sysLibs
                return {}

    def getParent(self, projectNode):
        parent = projectNode.find("mvn:parent", self.ns)
        return parent

    def findParentFile(self, parentNode, filePath):
        relativePath = parentNode.find("mvn:relativePath", self.ns)
        if not relativePath:
            relativePath = self.parentPathDefault

        parentDir = os.path.dirname(os.path.dirname(filePath))
        self.parsePom(parentDir + "/pom.xml")

    def gatherDependencies(self, dependencies):
        for dependency in dependencies:
            groupId = dependency.find("mvn:groupId", self.ns).text
            artifactId = dependency.find("mvn:artifactId", self.ns).text
            typeDef = dependency.find("mvn:type", self.ns)
            print(groupId + "." + artifactId)
            if typeDef is not None:
                print("Found nar dep")
                type = typeDef.text
                dep = mvnDep.MavenDependency(groupId, artifactId, "0.0.1-PLACEHOLDER", type)
                self.dependencies.append(dep)



