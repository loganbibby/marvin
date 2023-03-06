class MarvinException(Exception):
    code = None
    display = None

    def __str__(self):
        return self.display.format(**self.__dict__)


class InvalidToken(MarvinException):
    code = "invalid_token"
    display = "The MFA token you entered is invalid"


class InvalidTokenLength(InvalidToken):
    code = "invalid_token_length"
    display = "Your MFA token must be {length} digits"

    def __init__(self, length):
        self.length = length
