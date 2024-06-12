#!/usr/bin/env python3
"""
Emulates the Bash 'pushd' command
Usable with the 'with' statement

No 'popd' is needed as the __exit__() method
performs the 'popd' when the with statement
goes out of scope.
"""
import os
from lib.colortext import ANSIColor

class pushd():
    def __init__(self, _dir, _verbose=False):
        self.prevdir = os.getcwd()
        self._dir = _dir
        self.verbose = _verbose

    def __enter__(self):
        os.chdir(self._dir)
        if self.verbose:
            print(ANSIColor("cyan", "PUSHD -->", os.getcwd()))

    def __exit__(self, *args):
        os.chdir(self.prevdir)
        if self.verbose:
            print(ANSIColor("cyan", "POPD -->", os.getcwd()))
