"""
    module to configure pagination
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class PaginationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding pagination details to the request state.
    """

    def __init__(self, app, default_limit=10):
        """
        Initailize pagination with default limit
        """
        super().__init__(app)
        self.default_limit = default_limit

    async def dispatch(self, request: Request, call_next):
        """
        Extracting 'page' and 'limit' from query parameters
        store it in request state
        """
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", self.default_limit))

        # Ensure values are valid
        page = max(page, 1)
        limit = max(limit, 1)

        # Calculate pagination indices
        start_index = (page - 1) * limit
        end_index = start_index + limit

        # Store pagination details in `request.state`
        request.state.pagination = {
            "page": page,
            "limit": limit,
            "start_index": start_index,
            "end_index": end_index,
        }

        # Proceeding to the next middleware or endpoint
        response = await call_next(request)
        return response
