# Taken from https://github.com/tiangolo/fastapi/issues/4420
"""Middleware for security."""
import typing
from collections import OrderedDict

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from .config.api_security import CSPConfig



class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app: FastAPI, csp: typing.Optional[CSPConfig], additional_headers: typing.Optional[typing.Dict[str, str]]) -> None:
        """Init SecurityHeadersMiddleware.

        :param app: FastAPI instance
        :param no_csp: If no CSP should be used;
            defaults to :py:obj:`False`
        """
        super().__init__(app)
        headers = {}
        if csp is not None:
            headers["Content-Security-Policy"] = self._parse_policy(csp)
        if additional_headers is not None:
            headers.update(additional_headers)
        self.headers = headers

    @staticmethod
    def _parse_policy(policy: CSPConfig) -> str:
        """Parse a given policy dict to string."""
        if isinstance(policy, str):
            # parse the string into a policy dict
            policy_string = policy
            policy = OrderedDict()

            for policy_part in policy_string.split(";"):
                policy_parts = policy_part.strip().split(" ")
                policy[policy_parts[0]] = " ".join(policy_parts[1:])

        policies = []
        for section, content in policy.items():
            if not isinstance(content, str):
                content = " ".join(content)
            policy_part = f"{section} {content}"

            policies.append(policy_part)

        parsed_policy = "; ".join(policies)

        return parsed_policy

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Dispatch of the middleware.

        :param request: Incoming request
        :param call_next: Function to process the request
        :return: Return response coming from from processed request
        """
        response = await call_next(request)
        response.headers.update(self.headers.copy())

        return response