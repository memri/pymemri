from typing import List

from pydantic import BaseModel


class TriggerReq(BaseModel):
    item_ids: List[str]
    trigger_id: str
