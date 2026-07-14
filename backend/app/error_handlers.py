from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class InsufficientBudgetError(Exception):
    pass


class AgentExecutionError(Exception):
    pass


class RepositoryCloneError(Exception):
    pass


class RateLimitExceededError(Exception):
    pass


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error"},
    )


async def budget_exception_handler(request: Request, exc: InsufficientBudgetError):
    return JSONResponse(
        status_code=402,
        content={"detail": str(exc)},
    )


async def agent_exception_handler(request: Request, exc: AgentExecutionError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


async def repo_exception_handler(request: Request, exc: RepositoryCloneError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )
