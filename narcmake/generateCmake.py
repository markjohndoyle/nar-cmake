import sys
import logging
import os
from narcmake import pomParser as pom
from narcmake import cmakeBuilder as cmake

__author__ = 'Mark'


def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    log = logging.getLogger("Nar2Cmake")

    pomFile = sys.argv[1]
    log.info("Parsing pom " + pomFile)

    parser = pom.PomParser()
    parser.parsePom(pomFile, sys.argv[2])

    log.debug("Final dependency list ----------")
    for dep in parser.dependencies:
        log.debug(str(dep))
    log.debug("---------------")

    log.info("Building CMakeLists.txt file...")
    cmakebuilder = cmake.CmakeBuilder(parser, os.path.dirname(pomFile))
    cmakebuilder.build()

    log.info("Success!")


if __name__ == '__main__':
    main()