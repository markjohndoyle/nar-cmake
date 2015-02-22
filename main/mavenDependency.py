__author__ = 'Mark'

import platform


class MavenDependency:
    def __init__(self, groupId, artifactId, version, artifactType="jar"):
        self.groupId = groupId
        self.artifactId = artifactId
        self.type = artifactType
        self.version = version


    def getAol(self, linker) -> str:
        os = platform.system()
        arch = platform.machine().lower()
        return self.artifactId + "-" + self.version + "-" + arch + "-" + os + "-" + linker + "-shared"