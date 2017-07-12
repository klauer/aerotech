class AeroException(Exception):
    ...


class WriteFailureException(AeroException):
    def __init__(self, expected, read):
        self.expected = expected
        self.read = read


class AeroResponseException(AeroException):
    def __init__(self, response_text):
        self.response_text = response_text


class FailureResponseException(AeroResponseException):
    ...


class FaultResponseException(AeroResponseException):
    ...


class TimeoutResponseException(AeroResponseException):
    ...


class UnknownResponseException(AeroResponseException):
    def __init__(self, code, response_text):
        self.code = code
        self.response_text = response_text
