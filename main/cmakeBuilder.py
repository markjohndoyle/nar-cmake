__author__ = 'Mark'


class CmakeBuilder:
    def build(self, parser):
        makeFile = open("CMakeLists.txt", "w")

        makeFile.write("make_minimum_required (VERSION 2.6)\n")
        makeFile.write("project (" + parser.groupId + "." + parser.artifactId + ")\n")
        makeFile.write("add_executable(" + parser.artifactId + "-" + parser.version + " ${SOURCES})\n")