import xml.etree.cElementTree as ETree
import os
import logging

from main import mavenDependency as mvnDep


__author__ = 'Mark'


class PomParser:
    NAR_PLUG = "nar-maven-plugin"
    ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
    parentPathDefault = "../"

    dependencyVersions = {}
    dependencies = []
    buildOptions = {
        "compiler": "g++",
        "linker": "g++",
        "debug": True,
        "compilerFlags": {"-std=c++11"},
        "sysLibs": set(),
        "output": "executable"}

    properties = {}


    # Parses the pom pulling out nar specifics.
    def parsePom(self, filepath, projectRoot):
        self.log = logging.getLogger(__name__)

        self.log.debug("Parsing pom " + filepath)
        self.projectRoot = projectRoot

        self.modulePath = os.path.dirname(filepath)
        sourcePath = self.modulePath + "/src/main/c++"
        if os.path.isdir(sourcePath):
            self.buildOptions["srcPath"]  = sourcePath
        else:
            self.log.debug(filepath + " + is a parent pom")

        includePath = self.modulePath + "/src/main/include"
        if os.path.isdir(includePath):
            self.buildOptions["incPath"]  = includePath
        else:
            self.log.debug(filepath + " + is a parent pom")

        tree = ETree.parse(filepath)
        projectElem = tree.getroot()

        parent = self.getParent(projectElem)
        if parent:
            parentFile = self.parseParentPom(parent, filepath)
        else:
            self.rootPom = filepath


        find = projectElem.find("mvn:version", self.ns)
        if find is not None:
            self.version = find.text
            self.log.debug("Set project version to " + self.version)

        self.gatherProperties(projectElem)

        plugins = projectElem.findall("mvn:build/mvn:pluginManagement/mvn:plugins/mvn:plugin", self.ns)
        self.gatherNarPluginConfig(plugins)
        plugins = projectElem.findall("mvn:build/mvn:plugins/mvn:plugin", self.ns)
        self.gatherNarPluginConfig(plugins)

        dependencyManagements = projectElem.findall("mvn:dependencyManagement/mvn:dependencies/mvn:dependency", self.ns)
        self.gatherAllNarDepManagement(dependencyManagements)

        dependencies = projectElem.findall("mvn:dependencies/mvn:dependency", self.ns)
        self.gatherDependencies(dependencies)

        self.groupId = projectElem.find("mvn:groupId", self.ns).text
        self.artifactId = projectElem.find("mvn:artifactId", self.ns).text

    def gatherNarPluginConfig(self, pluginsNode):
        for plugin in pluginsNode:
            artifactId = plugin.find("mvn:artifactId", self.ns)
            if artifactId.text == self.NAR_PLUG:
                self.gatherSysLibs(plugin)
                self.gatherLibraries(plugin)

    def gatherSysLibs(self, plugin):
        sysLibsNode = plugin.findall("mvn:configuration/mvn:linker/mvn:sysLibs/mvn:sysLib/mvn:name", self.ns)
        sysLibs = self.buildOptions["sysLibs"]
        for sysLib in sysLibsNode:
            sysLibs.add(sysLib.text)
        self.buildOptions["sysLibs"] = sysLibs

    def gatherLibraries(self, plugin):
        libsElem = plugin.findall("mvn:configuration/mvn:libraries/mvn:library", self.ns)
        for lib in libsElem:
            outLib = lib.find("mvn:type", self.ns)
            self.buildOptions["output"] = outLib.text

    def getParent(self, projectNode):
        parent = projectNode.find("mvn:parent", self.ns)
        return parent

    def parseParentPom(self, parentNode, filePath):
        relativePath = parentNode.find("mvn:relativePath", self.ns)
        if not relativePath:
            relativePath = self.parentPathDefault
        parentDir = os.path.dirname(os.path.dirname(filePath))
        self.parsePom(parentDir + "/pom.xml", self.projectRoot)

    def gatherDependencies(self, dependencies):
        for dependency in dependencies:
            typeDef = dependency.find("mvn:type", self.ns)
            if typeDef is not None:
                groupId = dependency.find("mvn:groupId", self.ns).text
                artifactId = dependency.find("mvn:artifactId", self.ns).text
                type = typeDef.text
                versionDef = dependency.find("mvn:version", self.ns)
                if versionDef is not None:
                    version = versionDef.text
                else:
                    managedVersion = self.dependencyVersions[groupId + "." + artifactId]
                    if managedVersion is not None:
                        version = managedVersion
                    else:
                        self.log.warn(artifactId + "." + artifactId + " dependency has no version, ignoring")
                        return
                dep = mvnDep.MavenDependency(groupId, artifactId, version, type)
                self.dependencies.append(dep)
                self.log.debug("Found nar dependency: " + dep.getAol("gpp"))

    def gatherAllNarDepManagement(self, dependencyManagements):
        for management in dependencyManagements:
            typeDef = management.find("mvn:type", self.ns)
            if typeDef is not None:
                type = typeDef.text
                if type == "nar":
                    groupId = management.find("mvn:groupId", self.ns).text
                    artifactId = management.find("mvn:artifactId", self.ns).text
                    version = management.find("mvn:version", self.ns).text
                    if version.startswith("${"):
                        if version == "${project.version}":
                            version = self.version
                        else:
                            version = self.properties[version]
                    self.dependencyVersions[groupId + "." + artifactId] = version

    def gatherProperties(self, projectElem):
        for prop in projectElem.findall("mvn:properties/*", self.ns):
            mvnNamespace = "{" + self.ns["mvn"] + "}"
            if prop.tag.startswith(mvnNamespace):
                propKey = "${" + prop.tag.replace(mvnNamespace, "", 1) + "}"
                self.properties[propKey] = prop.text;







