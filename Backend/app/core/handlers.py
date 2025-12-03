"""
Exception Handlers
Global exception handlers for FastAPI
Ensures consistent error responses across the application
"""

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.core.exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ServiceException,
    RepositoryException,
    RateLimitException
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle all application-specific exceptions"""
        logger.warning(
            f"AppException: {exc.code} - {exc.message}",
            extra={"details": exc.details, "path": request.url.path}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
        """Handle not found exceptions"""
        logger.info(f"Resource not found: {exc.message}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=404,
            content=exc.to_dict()
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException) -> JSONResponse:
        """Handle validation exceptions"""
        logger.info(f"Validation error: {exc.message}", extra={"details": exc.details})
        return JSONResponse(
            status_code=422,
            content=exc.to_dict()
        )
    
    @app.exception_handler(AuthenticationException)
    async def auth_exception_handler(request: Request, exc: AuthenticationException) -> JSONResponse:
        """Handle authentication exceptions"""
        logger.warning(f"Authentication failed: {exc.message}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=401,
            content=exc.to_dict(),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @app.exception_handler(AuthorizationException)
    async def authz_exception_handler(request: Request, exc: AuthorizationException) -> JSONResponse:
        """Handle authorization exceptions"""
        logger.warning(f"Authorization denied: {exc.message}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=403,
            content=exc.to_dict()
        )
    
    @app.exception_handler(RateLimitException)
    async def rate_limit_handler(request: Request, exc: RateLimitException) -> JSONResponse:
        """Handle rate limit exceptions"""
        logger.info(f"Rate limit exceeded: {request.client.host if request.client else 'unknown'}")
        response = JSONResponse(
            status_code=429,
            content=exc.to_dict()
        )
        if "retry_after_seconds" in exc.details:
            response.headers["Retry-After"] = str(exc.details["retry_after_seconds"])
        return response
    
    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors"""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.info(f"Request validation error: {errors}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors}
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle standard HTTP exceptions"""
        logger.warning(
            f"HTTP error {exc.status_code}: {exc.detail}",
            extra={"path": request.url.path}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail),
                    "details": {}
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle any uncaught exceptions"""
        logger.exception(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            extra={"path": request.url.path}
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {}
                }
            }
        )
    
    logger.info("Exception handlers registered")
