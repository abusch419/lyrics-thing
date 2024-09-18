from fastapi import APIRouter
from pydantic import BaseModel

api_router = APIRouter()


class HelloWorldResponse(BaseModel):
    message: str


@api_router.get("/", response_model=HelloWorldResponse)
def get_root():
    return {"message": "Hello world!"}
