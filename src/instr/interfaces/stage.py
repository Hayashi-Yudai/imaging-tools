from abc import ABCMeta, abstractmethod


class stages(metaclass=ABCMeta):
    """
    The interface for stage controllers. This class should implement
    __enter__ and __exit__ methods for using context manager.

    """
    def __enter__(self):
        return self


    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError


    @abstractmethod
    def initialize(self):
        raise NotImplementedError


    @abstractmethod
    def wait_while_busy(self):
        raise NotImplementedError


    @abstractmethod
    def move(self, angle, axis):
        raise NotImplementedError
