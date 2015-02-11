#! /usr/bin/env python

class IrisInputException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class IrisNoSuchAlgorithmException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class IrisTesseractException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class IrisOcropusException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class IrisOcropusException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class IrisStorageViolationException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class IrisNoSuchStorageBin(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)
