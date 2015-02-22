__author__ = 'Mark'


class CmakeBuilder:
    def __init__(self, pomParser):
        self.makeFile = open("CMakeLists.txt", "w")
        self.groupId = pomParser.groupId
        self.artifactId = pomParser.artifactId
        self.version = pomParser.version
        self.output = pomParser.buildOptions["output"]


    def build(self):
        self.makeFile.write("make_minimum_required (VERSION 2.6)\n")
        self.makeFile.write("project (" + self.groupId + "." + self.artifactId + ")\n")

        self.addType()


    def addType(self):
        if self.output == "executable":
            self.makeFile.write("add_executable(" + self.artifactId + "-" + self.version + " ${SOURCES})\n")
        elif self.output == "shared":
            self.makeFile.write("add_library(" + self.artifactId + "-" + self.version + " ${SOURCES})\n")
        elif self.output == "static":
            self.makeFile.write("add_library(" + self.artifactId + "-" + self.version + " ${SOURCES})\n")
        else:
            raise Exception("Unknown output type " + self.output)



