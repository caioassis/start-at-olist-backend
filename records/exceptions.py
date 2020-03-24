from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_422_UNPROCESSABLE_ENTITY


class UnprocessableEntityError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY


class InvalidDatePeriodException(BaseException):
    """
    Exception raised when input dates are invalid, either None or starting date later than ending date.
    """
    pass
