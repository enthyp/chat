from abc import ABC, abstractmethod


class Model(ABC):
    @abstractmethod
    def process(self, msg):
        """
        Returns whatever metric you choose, e.g. a list of probabilities that
        given message contains racial insults, death threats and so on.
        :param msg: one line string
        :return: a list of numbers from [0,1]
        """
        raise NotImplementedError("Subclasses must implement this method!")
