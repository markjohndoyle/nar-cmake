import sys
import logging
import os
from main import pomParser as pom
from main import cmakeBuilder as cmake

__author__ = 'Mark'


def main():
    logging.basicConfig(level="DEBUG")
    log = logging.getLogger("Nar2Cmake")
    pomFile = sys.argv[1]
    log.info("Parsing pom " + pomFile)

    parser = pom.PomParser()
    parser.parsePom(pomFile, sys.argv[2])

    log.info("Building cmake file...")
    cmakebuilder = cmake.CmakeBuilder(parser, os.path.dirname(pomFile))
    cmakebuilder.build()

    log.info("Success!")


if __name__ == '__main__':
    main()