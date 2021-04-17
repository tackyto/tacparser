class TacParserException(Exception):
    """
    Base class for exceptions in this module.
    """
    pass


class ParseException(TacParserException):
    def __init__(self, message:str) -> None:
        self.__msg = message

    def __repr__(self) -> str:
        return "ParseException({})".format(repr(self.__msg))

    def __str__(self) -> str:
        return self.__repr__()


