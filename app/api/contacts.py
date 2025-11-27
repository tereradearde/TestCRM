from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_session
from ..services.allocation import AllocationResult, choose_operator_for_source

router = APIRouter()


def _get_source_with_assignments(db: Session, source_id: int) -> models.Source:
    source = (
        db.query(models.Source)
        .options(joinedload(models.Source.assignments).joinedload(models.SourceOperatorAssignment.operator))
        .filter(models.Source.id == source_id)
        .one_or_none()
    )
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


def _get_or_create_lead(db: Session, external_id: str, name: str | None) -> models.Lead:
    lead = db.query(models.Lead).filter(models.Lead.external_id == external_id).one_or_none()
    if lead:
        if name and not lead.name:
            lead.name = name
            db.add(lead)
        return lead

    lead = models.Lead(external_id=external_id, name=name)
    db.add(lead)
    db.flush()
    return lead


def _to_contact_read(contact: models.Contact) -> schemas.ContactRead:
    return schemas.ContactRead(
        id=contact.id,
        lead_id=contact.lead_id,
        source_id=contact.source_id,
        operator_id=contact.operator_id,
        operator_name=contact.operator.name if contact.operator else None,
        status=contact.status,
        message=contact.message,
        created_at=contact.created_at,
    )


@router.post("/", response_model=schemas.ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(payload: schemas.ContactCreate, db: Session = Depends(get_session)) -> schemas.ContactRead:
    source = _get_source_with_assignments(db, payload.source_id)
    lead = _get_or_create_lead(db, payload.lead_external_id, payload.lead_name)

    allocation: AllocationResult = choose_operator_for_source(db, source)
    operator_id = allocation.operator.id if allocation.operator else None

    contact = models.Contact(
        lead_id=lead.id,
        source_id=source.id,
        operator_id=operator_id,
        message=payload.message,
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    contact = (
        db.query(models.Contact)
        .options(joinedload(models.Contact.operator))
        .filter(models.Contact.id == contact.id)
        .one()
    )

    return _to_contact_read(contact)


@router.get("/", response_model=List[schemas.ContactWithLeadRead])
def list_contacts(db: Session = Depends(get_session)) -> List[schemas.ContactWithLeadRead]:
    contacts = (
        db.query(models.Contact)
        .options(
            joinedload(models.Contact.lead),
            joinedload(models.Contact.operator),
            joinedload(models.Contact.source),
        )
        .order_by(models.Contact.created_at.desc())
        .all()
    )

    return [
        schemas.ContactWithLeadRead(
            id=contact.id,
            lead_id=contact.lead_id,
            lead_external_id=contact.lead.external_id,
            lead_name=contact.lead.name,
            source_id=contact.source_id,
            source_name=contact.source.name,
            operator_id=contact.operator_id,
            operator_name=contact.operator.name if contact.operator else None,
            status=contact.status,
            message=contact.message,
            created_at=contact.created_at,
        )
        for contact in contacts
    ]


