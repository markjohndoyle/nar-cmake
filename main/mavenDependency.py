__author__ = 'Mark'

import platform


class MavenDependency:
    def __init__(self, groupId, artifactId, version, artifactType="jar"):
        self.groupId = groupId
        self.artifactId = artifactId
        self.type = artifactType
        self.version = version
        self.libType = "shared"


    def getFullNarName(self, linker) -> str:
        arch = platform.machine().lower()
        os = platform.system()
        return self.artifactId + "-" + self.version + "-" + arch + "-" + os + "-" + linker + "-" + self.libType

    def getAol(self, linker) -> str:
        return platform.machine().lower() + "-" + platform.system() + "-" + linker
