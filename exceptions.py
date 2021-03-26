'''
Module for defining custom Exceptions, following standard conventions.
'''

class ProcessInterruptionError(Exception):
    ''' Error raised when the process is deliveratly interrupted by the user '''
    pass

class LogFileFormatError(Exception):
    ''' Error raised when the format of the log file is improper'''
    pass

class ProcessTimeoutError(Exception):
    ''' Raised when a hardware condition is not met after a specified timeout period. '''
    pass
