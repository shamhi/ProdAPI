import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, ValidationException
from starlette.middleware.base import RequestResponseEndpoint
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.config import Config
from app.db.base import Base
from app.routers import public_router, private_router
from app.utils.models import ErrorResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_all_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=ErrorResponse(reason=exc.detail).dict())


@app.exception_handler(404)
async def not_found_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=ErrorResponse(reason=exc.detail).dict())


@app.exception_handler(ValidationException)
async def validation_exception_handler(_: Request, exc: ValidationException):
    return JSONResponse(status_code=422, content=ErrorResponse(reason=exc.errors()).dict())


# print(os.environ)
# url = f"postgresql+asyncpg://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DATABASE}" if not Config.POSTGRES_CONN else Config.POSTGRES_CONN

# engine = create_async_engine(url=url, echo=False, future=True)
# db_pool = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next: RequestResponseEndpoint):
    async with db_pool() as db_session:
        request.state.db_session = db_session
        response = await call_next(request)

    return response


def main():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://editor-next.swagger.io"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router=public_router)
    app.include_router(router=private_router)

    import uvicorn
    uvicorn.run(app, host=Config.SERVER_HOST, port=Config.SERVER_PORT)


if __name__ == "__main__":
    main()
