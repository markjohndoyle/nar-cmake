__author__ = 'Mark'

import platform

# Nar dependency really, rename.
class MavenDependency:
    def __init__(self, groupId, artifactId, version, artifactType="nar", type="shared", local=False, path=""):
        self.groupId = groupId
        self.artifactId = artifactId
        self.type = artifactType
        self.version = version
        self.libType = type
        self.foundLocal = local
        self.path = path


    def getFullNarName(self, linker) -> str:
        arch = platform.machine().lower()
        os = platform.system()
        return self.artifactId + "-" + self.version + "-" + arch + "-" + os + "-" + linker + "-" + self.libType

    def getAol(self, linker) -> str:
        return platform.machine().lower() + "-" + platform.system() + "-" + linker

    def __str__(self):
        return " ".join(filter(None, [self.groupId + "." + self.artifactId + "-" + self.version, self.path]))

