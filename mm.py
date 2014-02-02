#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from mm.request import MavensMateRequestHandler

def main():
    MavensMateRequestHandler().execute()

if  __name__ == '__main__':
    main()