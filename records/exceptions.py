class InvalidDatePeriodException(BaseException):
    """
    Exception raised when input dates are invalid, either None or starting date later than ending date.
    """
    pass
