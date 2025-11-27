from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_session

router = APIRouter()


@router.get("/", response_model=List[schemas.LeadWithContactsRead])
def list_leads(db: Session = Depends(get_session)) -> List[schemas.LeadWithContactsRead]:
    leads = (
        db.query(models.Lead)
        .options(
            joinedload(models.Lead.contacts).joinedload(models.Contact.operator),
            joinedload(models.Lead.contacts).joinedload(models.Contact.source),
        )
        .order_by(models.Lead.created_at.desc())
        .all()
    )

    result: List[schemas.LeadWithContactsRead] = []
    for lead in leads:
        contacts = [
            schemas.ContactRead(
                id=contact.id,
                lead_id=contact.lead_id,
                source_id=contact.source_id,
                operator_id=contact.operator_id,
                operator_name=contact.operator.name if contact.operator else None,
                status=contact.status,
                message=contact.message,
                created_at=contact.created_at,
            )
            for contact in sorted(lead.contacts, key=lambda contact: contact.created_at, reverse=True)
        ]
        result.append(
            schemas.LeadWithContactsRead(
                id=lead.id,
                external_id=lead.external_id,
                name=lead.name,
                created_at=lead.created_at,
                contacts=contacts,
            )
        )
    return result


