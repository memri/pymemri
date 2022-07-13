from typing import Any, Dict, Union
from pydantic import BaseModel, Field

class TriggerReq(BaseModel):
    item_id: str = Field(alias="itemId")
    trigger_id: str = Field(alias="triggerId")


class FilterDaily(BaseModel):
    time: str

class FilterBatch(BaseModel):
    batch: int

class RegisterReq(BaseModel):
    trigger_id: str = Field(alias="triggerId")
    # TODO: that evaluates egarly if filter is like: {"time": "12:12", "batch": 123} -
    # it will fit as FilterDaily, even though it's invalid filter
    filter: Union[FilterDaily, FilterBatch]
