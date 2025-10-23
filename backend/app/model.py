from pydantic import BaseModel

class PeopleRequest(BaseModel):
    keyword: str
    location: str
