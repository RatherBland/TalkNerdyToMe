import os


class Conf:
    def __init__(self):
        '''SMMRY API Key goes below.'''
        self.key = os.environ.get('SMMRY_KEY')