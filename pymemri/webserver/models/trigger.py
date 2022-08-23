from pydantic import BaseModel

class TriggerReq(BaseModel):
    item_id: str
    trigger_id: str
