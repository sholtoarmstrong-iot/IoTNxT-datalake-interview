from fastapi.exceptions import HTTPException
import typing

if typing.TYPE_CHECKING:
    from requests import Response
    from aiohttp import ClientResponse

class TracebackAutoFill: pass
class TracebackSkip: pass

class NavigatorAPIException(HTTPException):
    def __init__(
        self, 
        user_message: str, 
        status_code: int = 500,
        detail: str = None, 
        stack_trace: str = TracebackAutoFill, 
        headers: typing.Optional[typing.Dict[str, typing.Any]] = None,
        hide_logs: bool = False
    ):
        super().__init__(status_code, detail, headers)
        self.hide_logs = hide_logs
        self.user_message = user_message
        if stack_trace == TracebackAutoFill:
            import traceback
            self.stack_trace = traceback.format_exc(limit=100)
        elif stack_trace == TracebackSkip:
            self.stack_trace = None
        else:
            self.stack_trace = stack_trace
    def get_dict(self):
        return {
            "detail": self.detail, 
            "user_message": self.user_message, 
            "stack_trace": self.stack_trace
        }

class AuthenticationException(NavigatorAPIException):
    def __init__(self, 
        user_message: str = "Access Denied", 
        detail: str = "The user does not have access to perform the desired operation.", 
        status_code: int = 401, 
        headers: typing.Optional[typing.Dict[str, typing.Any]] = None
    ):
        super().__init__(user_message, status_code, detail, TracebackSkip, headers, hide_logs=True)


class PermissionException(AuthenticationException):
    def __init__(self, 
        permission: str,
        user_message: str = "Access Denied", 
        headers: typing.Optional[typing.Dict[str, typing.Any]] = None
    ):
        super().__init__(user_message, f"Unauthorized: No Access to {permission}", headers=headers)

class AttemptToCrossAccountException(AuthenticationException):
    def __init__(self, 
        user_message: str = "Access Denied", 
        detail: str = "User requires 'Can Cross Account' privileges to perform the action.", 
        headers: typing.Optional[typing.Dict[str, typing.Any]] = None
    ):
        super().__init__(user_message, detail, headers=headers)


FoundryAPIException = NavigatorAPIException

class CommonExceptionBase(NavigatorAPIException):
    __DEFAULT_STATUS_CODE__ = 500
    __DEFAULT_DETAIL__ = "An unexpected error has occured"
    __DEFAULT_USER_MESSAGE__ = "An unexpected error has occured"
    __TRACEBACK__ = TracebackAutoFill
    def __init__(self, 
        user_message: str = None, 
        detail: str = None, 
        status_code: int = None, 
        headers: typing.Optional[typing.Dict[str, typing.Any]] = None
    ):
        if detail is None:
            detail = self.__DEFAULT_DETAIL__
        if user_message is None:
            user_message = self.__DEFAULT_USER_MESSAGE__
        if status_code is None:
            status_code = self.__DEFAULT_STATUS_CODE__
        super().__init__(user_message, status_code, detail, self.__TRACEBACK__, headers, hide_logs=False)

class ValueValidationError(NavigatorAPIException):
    __DEFAULT_STATUS_CODE__ = 400
    __DEFAULT_DETAIL__ = ""
    def __init__(self, 
        found: typing.Optional[str] = None, 
        expected: typing.Optional[str] = None, 
        detail: typing.Optional[str] = None, 
        user_message: str = "Unexpected value Error", 
        status_code: int = 400, 
        headers: typing.Optional[typing.Dict[str, typing.Any]] = None
    ):
        if detail is None:
            if expected is None and found is None:
                detail = self.__DEFAULT_DETAIL__
            elif expected is None:
                detail = f"Found unexpected value: {found}"
            elif found is None:
                detail = f"Expected: {expected}"
            else:
                detail = f"Found unexpected value: {found}. Expected {expected}."

        super().__init__(user_message, status_code, detail, TracebackSkip, headers, hide_logs=True)

class ConfigurationError(CommonExceptionBase):
    __DEFAULT_STATUS_CODE__ = 500
    __DEFAULT_DETAIL__ = "Issue found with configuration."


class ExternalAPIRequestConnectionError(CommonExceptionBase):
    __DEFAULT_STATUS_CODE__ = 503
    __DEFAULT_DETAIL__ = "Could not connect to {url}"
    __DEFAULT_USER_MESSAGE__ = "A temporary error occurred. Please try again."
    def __init__(self, url:str="an external api.", user_message: str = None, detail: str = None, status_code: int = None, headers: typing.Optional[typing.Dict[str, typing.Any]] = None):
        if status_code is None:
            status_code = self.__DEFAULT_STATUS_CODE__
        if detail is None:
            detail = self.__DEFAULT_DETAIL__.format(url=url)
        super().__init__(user_message, detail, status_code, headers)

class ExternalAPIRequestError(CommonExceptionBase):
    __DEFAULT_STATUS_CODE__ = 500
    __DEFAULT_DETAIL__ = "Received a '{error_code_text}' response from {host} with response data: {data}."
    __DEFAULT_USER_MESSAGE__ = "A temporary error occurred when requesting from an api. Please try again."
    def __init__(self, data:str, host="an external api", ext_status_code: int = None, user_message: str = None, detail: str = None, status_code: int = None, headers: typing.Optional[typing.Dict[str, typing.Any]] = None):
        if ext_status_code is None:
            ext_status_code = self.__DEFAULT_STATUS_CODE__
        if status_code is None:
            status_code = ext_status_code
        if detail is None:
            from requests import status_codes
            detail = self.__DEFAULT_DETAIL__.format(
                data=data,
                host=host,
                error_code_text=status_codes._codes.get(status_code, ("Unknown",))[0]
            )
        super().__init__(user_message, detail, status_code, headers)
    @staticmethod
    def raise_from_requests_response(r: 'Response', **kwargs):
        from requests import JSONDecodeError as RequestsJSONDecodeError
        if r.ok(): return
        dta = r.text
        try:
            dta = r.json()
        except RequestsJSONDecodeError as e:
            pass
        raise ExternalAPIRequestError(dta, host=r.url, ext_status_code=r.status_code, **kwargs)
    @staticmethod
    async def raise_from_aiohttp_response(r: 'ClientResponse', **kwargs):
        from json import JSONDecodeError
        from aiohttp import ContentTypeError

        if r.ok: return
        dta = None
        try:
            dta = await r.json()
        except (JSONDecodeError,ContentTypeError) as e:
            pass
        try:
            if dta is None:
                dta = await r.text()
        except UnicodeError as e:
            pass
        if dta is None:
            dta = "**Unable to Decode**"

        raise ExternalAPIRequestError(dta, host=r.url, ext_status_code=r.status, **kwargs)

class ExternalAPIUnexpectedResponseError(CommonExceptionBase):
    __DEFAULT_STATUS_CODE__ = 500
    __DEFAULT_DETAIL__ = "Received an unexpected response from external API"
    __DEFAULT_USER_MESSAGE__ = "A temporary error occurred. Please try again."