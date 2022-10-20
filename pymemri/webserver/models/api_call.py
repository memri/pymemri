from pydantic import BaseModel


class CallReq(BaseModel):
    function: str
    args: dict
