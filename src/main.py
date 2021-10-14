#!/usr/bin/env python3
from Application import Application
import os
import sys

if __name__ == '__main__':
    try:
        app = Application(sys.argv[0], sys.argv[1:])
        app.run()
    except KeyboardInterrupt:
        print('') # Force new-line at exit
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)