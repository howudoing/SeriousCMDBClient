import os,sys
from core.argv_processor import ArgvProcessor


BASEDIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

sys.path.append(BASEDIR)

if __name__ == '__main__':
    ArgvProcessor(sys.argv)

