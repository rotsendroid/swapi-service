from pydantic import BaseModel


class BaseSuccessfullResponse(BaseModel):
    message: str = "Operation successful"


class BaseErrorResponse(BaseModel):
    message: str
    details: str
    status_code: int
    error_code: str
