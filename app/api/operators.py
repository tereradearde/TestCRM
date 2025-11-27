from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_session

router = APIRouter()


def _get_operator(db: Session, operator_id: int) -> models.Operator:
    operator = db.get(models.Operator, operator_id)
    if operator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")
    return operator


def _count_active_contacts(db: Session, operator_id: int) -> int:
    return (
        db.query(func.count(models.Contact.id))
        .filter(models.Contact.operator_id == operator_id, models.Contact.status == "active")
        .scalar()
        or 0
    )


@router.post("/", response_model=schemas.OperatorRead, status_code=status.HTTP_201_CREATED)
def create_operator(payload: schemas.OperatorCreate, db: Session = Depends(get_session)) -> schemas.OperatorRead:
    operator = models.Operator(**payload.dict())
    db.add(operator)
    db.commit()
    db.refresh(operator)
    current_load = _count_active_contacts(db, operator.id)
    return schemas.OperatorRead(
        id=operator.id,
        name=operator.name,
        active=operator.active,
        load_limit=operator.load_limit,
        created_at=operator.created_at,
        current_load=current_load,
    )


@router.get("/", response_model=List[schemas.OperatorRead])
def list_operators(db: Session = Depends(get_session)) -> List[schemas.OperatorRead]:
    operators = db.query(models.Operator).order_by(models.Operator.id).all()
    if not operators:
        return []

    operator_ids = [operator.id for operator in operators]
    loads = dict(
        db.query(models.Contact.operator_id, func.count(models.Contact.id))
        .filter(
            models.Contact.operator_id.in_(operator_ids),
            models.Contact.status == "active",
        )
        .group_by(models.Contact.operator_id)
        .all()
    )

    return [
        schemas.OperatorRead(
            id=operator.id,
            name=operator.name,
            active=operator.active,
            load_limit=operator.load_limit,
            created_at=operator.created_at,
            current_load=loads.get(operator.id, 0),
        )
        for operator in operators
    ]


@router.patch("/{operator_id}", response_model=schemas.OperatorRead)
def update_operator(
    operator_id: int, payload: schemas.OperatorUpdate, db: Session = Depends(get_session)
) -> schemas.OperatorRead:
    operator = _get_operator(db, operator_id)

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(operator, key, value)

    db.add(operator)
    db.commit()
    db.refresh(operator)
    current_load = _count_active_contacts(db, operator.id)
    return schemas.OperatorRead(
        id=operator.id,
        name=operator.name,
        active=operator.active,
        load_limit=operator.load_limit,
        created_at=operator.created_at,
        current_load=current_load,
    )


