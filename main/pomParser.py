import xml.etree.cElementTree as ETree
import os
import logging
from collections import namedtuple

from main import mavenDependency as mvnDep


__author__ = 'Mark'


class PomParser:
    NAR_PLUG = "nar-maven-plugin"
    ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
    parentPathDefault = "../"
    targetDir = "target"

    dependencyVersions = {}
    Dependency = namedtuple("Dependency", "mvnDep foundLocal localPath")
    dependencies = []
    projectLocalDependencies = []
    buildOptions = {
        "compiler": "g++",
        "linker": "g++",
        "debug": True,
        "compilerFlags": {"-std=c++11"},
        "sysLibs": set(),
        "output": "executable"
    }
    Module = namedtuple("module", "groupId artifactId path")
    localModules = []

    properties = {}

    def parsePom(self, filepath, projectRoot):
        self.log = logging.getLogger(__name__)
        self.log.debug("Parsing pom " + filepath)

        self.projectRoot = projectRoot
        self.projectPath = filepath

        tree = ETree.parse(filepath)
        self.projectElem = tree.getroot()

        rootParent = False
        # Here we get the parent element from the pom. If there is one then this is a child
        # pom and we need to parse the parent first.
        parent = self.getParent()
        if parent is not None:
            parentFile = self.parseParentPom(parent, filepath)
        else:
            rootParent = True

        self.projectElem = tree.getroot()

        self.gatherProperties()
        self.setProjectVersion()
        self.setSourcePath(filepath)
        self.setIncludePath(filepath)

        plugins = self.projectElem.findall("mvn:build/mvn:pluginManagement/mvn:plugins/mvn:plugin", self.ns)
        self.gatherNarPluginConfig(plugins)
        plugins = self.projectElem.findall("mvn:build/mvn:plugins/mvn:plugin", self.ns)
        self.gatherNarPluginConfig(plugins)

        dependencyManagements = self.projectElem.findall("mvn:dependencyManagement/mvn:dependencies/mvn:dependency",
                                                         self.ns)
        self.gatherAllNarDepManagement(dependencyManagements)

        dependenciesElem = self.projectElem.findall("mvn:dependencies/mvn:dependency", self.ns)
        print(filepath + " has " + str(len(dependenciesElem)) + " elements")
        self.gatherDependencies(dependenciesElem)

        if rootParent:
            print("Root parent " + filepath + " - gathering modules")
            self.gatherLocalModules(self.projectElem, self.projectPath)

        self.groupId = self.projectElem.find("mvn:groupId", self.ns).text
        self.artifactId = self.projectElem.find("mvn:artifactId", self.ns).text


    # Set the source path in build options - currently ignores source path in
    # the poms and uses conventional src/main/c++
    def setSourcePath(self, filepath):
        self.modulePath = os.path.dirname(filepath)
        sourcePath = os.path.join(self.modulePath, "src", "main", "c++")
        # Parses the pom pulling out nar specifics.
        if os.path.isdir(sourcePath):
            self.buildOptions["srcPath"] = sourcePath
            self.log.debug(filepath + " source directories set to " + sourcePath)
        else:
            self.log.debug(filepath + " does not have any source directories.")

    # Set the include path in build options - currently ignores include path in
    # the poms and uses conventional src/main/c++
    def setIncludePath(self, filepath):
        includePath = os.path.join(self.modulePath, "src", "main", "include")
        if os.path.isdir(includePath):
            self.buildOptions["incPath"] = includePath
            self.log.debug(filepath + " include directories set to " + includePath)
        else:
            self.log.debug(filepath + " does not have any source directories.")

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

    def getParent(self):
        print("Searching for parent in " + self.projectElem.find("mvn:artifactId", self.ns).text)
        parent = self.projectElem.find("mvn:parent", self.ns)
        return parent

    def parseParentPom(self, parentNode, filePath):
        relativePath = parentNode.find("mvn:relativePath", self.ns)
        if not relativePath:
            relativePath = self.parentPathDefault
        parentDir = os.path.dirname(os.path.dirname(filePath))
        self.parsePom(parentDir + "/pom.xml", self.projectRoot)

    def gatherDependencies(self, dependenciesElem):
        for dependency in dependenciesElem:
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
                self.dependencies.append(self.Dependency(mvnDep=dep, foundLocal=False, localPath=""))
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

    def gatherProperties(self):
        for prop in self.projectElem.findall("mvn:properties/*", self.ns):
            mvnNamespace = "{" + self.ns["mvn"] + "}"
            if prop.tag.startswith(mvnNamespace):
                propKey = "${" + prop.tag.replace(mvnNamespace, "", 1) + "}"
                self.properties[propKey] = prop.text;

    # Determines if the given dependency is local to this module, that is, is the
    # dependency a child module (a project in itself).
    def determineDependencyLocalities(self, moduleRootPath):
        if len(self.dependencies) > 0:
            self.log.debug("Determining dependency localities from module " + moduleRootPath)
        else:
            print("no dependencies found yet, not worth searching...")

        for dep in self.dependencies:
            mvnDep = dep.mvnDep
            # Search each subdirectory except target area TODO get target from pom in case it's altered
            modules = self.projectElem.findall("mvn:modules/mvn:module", self.ns)
            for module in modules:
                modPomPath = os.path.join(moduleRootPath, module.text, "pom.xml")
                if os.path.exists(modPomPath):
                    modulePom = open(modPomPath)
                    print("Found pom for module " + modPomPath)
                    # parse it and check it matches the mvnDep, if so we can reference the library in
                    # the cmake output dir
                    # TODO implement this, the module will have a target/cmake dir with it's build in.


    def setProjectVersion(self):
        find = self.projectElem.find("mvn:version", self.ns)
        if find is not None:
            self.version = find.text
            self.log.debug("Set project version to " + self.version)

    def gatherLocalModules(self, projectElem, projectPath):
        print("Looking for modules in " + projectElem.find("mvn:artifactId", self.ns).text)

        modules = projectElem.findall("mvn:modules/mvn:module", self.ns)
        profiles = projectElem.findall("mvn:profiles/mvn:profile", self.ns)
        activeProfile = self.findActiveProfile(profiles)
        if activeProfile is not None:
            print("Using profile")
            # we must use the modules list from the profile
            modules = activeProfile.findall("mvn:modules/mvn:module", self.ns)
        else:
            print("No profiles found.")

        for module in modules:
            print("Looking for module " + module.text)
            modPomPath = os.path.join(os.path.dirname(projectPath), module.text, "pom.xml")
            if os.path.exists(modPomPath):
                modPomRootElem = ETree.parse(modPomPath)
                packaging = modPomRootElem.find("mvn:packaging", self.ns).text
                if packaging == "nar":
                    print("Found nar module at " + modPomPath)
                    groupId = modPomRootElem.find("mvn:groupId", self.ns).text
                    artifactId = modPomRootElem.find("mvn:artifactId", self.ns).text
                    self.localModules.append(self.Module(groupId, artifactId, modPomPath))
                self.gatherLocalModules(modPomRootElem, modPomPath)
            else:
                self.log.warn(
                    "Module not found on disk - possibly not checked out from source control or the module entry in the pom is erroneous.")

    # Only returns the first active profile - multiple active profiles are not supported.
    def findActiveProfile(self, profiles):
        for profile in profiles:
            activation = profile.find("mvn:activation", self.ns)
            if activation is not None:
                active = activation.find("mvn:activeByDefault", self.ns)
                if active is not None:
                    return profile

