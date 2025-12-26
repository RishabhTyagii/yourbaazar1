from typing import Optional, Union
from rest_framework import exceptions
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str


class RequestNewTokenException(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("You can request a new token in {seconds} seconds.")
    default_code = "request_new_token"

    def __init__(self, seconds: Union[str, int], detail: Optional[str] = None, code: Optional[str] = None):
        if detail is None:
            detail = force_str(self.default_detail).format(seconds=seconds)
        super().__init__(detail, code)
