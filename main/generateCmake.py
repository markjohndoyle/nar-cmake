import sys

from main import pomParser

__author__ = 'Mark'


def main():
    print("Parsing root pom  " + sys.argv[1])
    parser = pomParser.PomParser()
    parser.parsePom(sys.argv[1])

    print(parser.narModule)


if __name__ == '__main__':
    main()