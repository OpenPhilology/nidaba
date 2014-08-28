#! /usr/bin/env python

class IrisInputException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class IrisNoSuchAlgorithmException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
