import abc

__author__ = 'ignacio'


class InformationSource(object):
    #
    # Information source abstract class

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def search(self, query):
        pass