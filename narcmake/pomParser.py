import xml.etree.cElementTree as ETree
import os
import logging
from collections import namedtuple

from narcmake import mavenDependency as mvnDep


__author__ = 'Mark'


class PomParser:
    NAR_PLUG = "nar-maven-plugin"
    ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
    parentPathDefault = "../"
    targetDir = "target"

    dependencyManagement = {}
    dependencies = {}
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
    localModules = {}
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
        self.gatherDependencies(dependenciesElem)

        if rootParent:
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
            # We now know it exists but cmake will work with relative paths so we don't want the module path
            self.buildOptions["srcPath"] = os.path.join("src", "main", "c++")
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
        parent = self.projectElem.find("mvn:parent", self.ns)
        return parent

    def parseParentPom(self, parentNode, filePath):
        relativePath = parentNode.find("mvn:relativePath", self.ns)
        if not relativePath:
            relativePath = self.parentPathDefault
        parentDir = os.path.dirname(os.path.dirname(filePath))
        self.parsePom(parentDir + "/pom.xml", self.projectRoot)

    def gatherDependencies(self, dependenciesElem):
        for depElem in dependenciesElem:
            artifactId = depElem.find("mvn:artifactId", self.ns).text
            groupId = depElem.find("mvn:groupId", self.ns).text
            typeDef = depElem.find("mvn:type", self.ns)
            scopeElem = depElem.find("mvn:scope", self.ns)
            if typeDef is not None and typeDef.text == "nar":
                type = typeDef.text
                versionDef = depElem.find("mvn:version", self.ns)
                if versionDef is not None:
                    version = versionDef.text
                else:
                    if groupId + "." + artifactId in self.dependencyManagement:
                        version = self.dependencyManagement[groupId + "." + artifactId]["version"]
                    else:
                        self.log.warn(artifactId + "." + artifactId + " dependency has no version, ignoring")
                        return
                dep = mvnDep.MavenDependency(groupId, artifactId, version, type)
                if groupId + "." + artifactId in self.localModules:
                    dep.foundLocal = True
                    dep.path = self.localModules[groupId + "." + artifactId]

                if scopeElem is not None:
                    dep.scope = scopeElem.text
                else:
                    if groupId + "." + artifactId in self.dependencyManagement:
                        dep.scope = self.dependencyManagement[groupId + "." + artifactId]["scope"]

                self.dependencies[str(dep)] = dep

                # Gather transitive dependencies.
                # Find pom of dependency - if it's external it's in the project's target area, otherwise it's in the
                # localPath
                if dep.foundLocal:
                    depProjectElem = ETree.parse(os.path.join(dep.path, "pom.xml"))
                    transitiveDeps = depProjectElem.findall("mvn:dependencies/mvn:dependency", self.ns)
                    if transitiveDeps is not None:
                        self.gatherDependencies(transitiveDeps)
                    else:
                        self.log.info("No transitive dependencies in " + depElem.getFullNarName("gpp"))


    def gatherAllNarDepManagement(self, dependencyManagements):
        for management in dependencyManagements:
            typeDef = management.find("mvn:type", self.ns)
            if typeDef is not None:
                type = typeDef.text
                if type == "nar":
                    groupId = management.find("mvn:groupId", self.ns).text
                    artifactId = management.find("mvn:artifactId", self.ns).text
                    version = management.find("mvn:version", self.ns).text
                    scopeElem = management.find("mvn:scope", self.ns)
                    scope = "compile" if scopeElem is None else scopeElem.text
                    if version.startswith("${"):
                        if version == "${project.version}":
                            version = self.version
                        else:
                            version = self.properties[version]
                    self.dependencyManagement[groupId + "." + artifactId] = {"version":version, "scope":scope}

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
                    # parse it and check it matches the mvnDep, if so we can reference the library in
                    # the cmake output dir
                    # TODO implement this, the module will have a target/cmake dir with it's build in.


    def setProjectVersion(self):
        find = self.projectElem.find("mvn:version", self.ns)
        if find is not None:
            self.version = find.text
            self.log.debug("Set project version to " + self.version)

    def gatherLocalModules(self, projectElem, projectPath):
        modules = projectElem.findall("mvn:modules/mvn:module", self.ns)
        profiles = projectElem.findall("mvn:profiles/mvn:profile", self.ns)
        activeProfile = self.findActiveProfile(profiles)
        if activeProfile is not None:
            # we must use the modules list from the profile
            modules = activeProfile.findall("mvn:modules/mvn:module", self.ns)

        for module in modules:
            modPomPath = os.path.join(os.path.dirname(projectPath), module.text, "pom.xml")
            if os.path.exists(modPomPath):
                modPomRootElem = ETree.parse(modPomPath)
                packaging = modPomRootElem.find("mvn:packaging", self.ns).text
                if packaging == "nar":
                    groupId = modPomRootElem.find("mvn:groupId", self.ns).text
                    artifactId = modPomRootElem.find("mvn:artifactId", self.ns).text
                    self.localModules[groupId + "." + artifactId] = os.path.dirname(modPomPath)
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

