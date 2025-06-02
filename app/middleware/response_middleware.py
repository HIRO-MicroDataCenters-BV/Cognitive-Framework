"""
Middleware for Cognitive Engine API
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.utils.response_utils import standard_response


class ResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware to format the response
    """

    async def dispatch(self, request, call_next):
        """
        to format the response
        :param request:
        :param call_next:
        :return:
        """
        response = await call_next(request)
        response_data = await response.json()
        return JSONResponse(
            standard_response(
                data=response_data,
                status_code=response.status_code,
                message=response.reason_phrase,
            )
        )
