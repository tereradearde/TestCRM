from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel, Field, validator


class OperatorBase(BaseModel):
    name: str = Field(..., max_length=100)
    active: bool = True
    load_limit: int = Field(ge=0, default=10)


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None
    load_limit: Optional[int] = Field(None, ge=0)


class OperatorRead(OperatorBase):
    id: int
    created_at: datetime
    current_load: int

    class Config:
        orm_mode = True


class SourceAssignmentInput(BaseModel):
    operator_id: int
    weight: int = Field(..., gt=0)


class SourceBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    assignments: Optional[Sequence[SourceAssignmentInput]] = None


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    assignments: Optional[Sequence[SourceAssignmentInput]] = None


class SourceAssignmentRead(BaseModel):
    operator_id: int
    operator_name: str
    weight: int

    class Config:
        orm_mode = True


class SourceRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    assignments: Sequence[SourceAssignmentRead]

    class Config:
        orm_mode = True


class LeadBase(BaseModel):
    external_id: str = Field(..., max_length=255)
    name: Optional[str] = Field(None, max_length=255)


class LeadRead(LeadBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ContactCreate(BaseModel):
    lead_external_id: str = Field(..., max_length=255)
    lead_name: Optional[str] = Field(None, max_length=255)
    source_id: int
    message: Optional[str] = Field(None, max_length=500)

    @validator("lead_external_id")
    def ensure_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("lead_external_id must not be empty")
        return value


class ContactRead(BaseModel):
    id: int
    lead_id: int
    source_id: int
    operator_id: Optional[int]
    operator_name: Optional[str]
    status: str
    message: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class ContactWithLeadRead(ContactRead):
    lead_external_id: str
    lead_name: Optional[str]
    source_name: str


class LeadWithContactsRead(LeadRead):
    contacts: Sequence[ContactRead]



