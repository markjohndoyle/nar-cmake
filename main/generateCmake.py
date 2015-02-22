import sys

from main import pomParser as pom
from main import cmakeBuilder as cmake

__author__ = 'Mark'


def main():
    print("Parsing root pom  " + sys.argv[1])
    parser = pom.PomParser()
    parser.parsePom(sys.argv[1], sys.argv[2])

    cmakebuilder = cmake.CmakeBuilder(parser)
    cmakebuilder.build()


if __name__ == '__main__':
    main()