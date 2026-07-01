from pydantic import BaseModel


class IssueCreate(BaseModel):
    title: str
    description: str
    category: str


class IssueUpdate(BaseModel):
    title: str
    description: str
    category: str
    status: str


class IssueResponse(BaseModel):
    id: int
    customer_id: int
    title: str
    description: str
    category: str
    status: str

    class Config:
        from_attributes = True