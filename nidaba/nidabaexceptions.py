#! /usr/bin/env python


class NibadaTaskException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaTickException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaStepException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaInputException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaNoSuchAlgorithmException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaInvalidParameterException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaTesseractException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaOcropusException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaStorageViolationException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)

class NibadaNoSuchStorageBin(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        Exception.__init__(self, status_code)
