from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_session

router = APIRouter()


def _get_source(db: Session, source_id: int) -> models.Source:
    source = (
        db.query(models.Source)
        .options(joinedload(models.Source.assignments).joinedload(models.SourceOperatorAssignment.operator))
        .filter(models.Source.id == source_id)
        .one_or_none()
    )
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


def _ensure_operator_exists(db: Session, operator_id: int) -> None:
    if db.get(models.Operator, operator_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Operator {operator_id} does not exist",
        )


def _apply_assignments(db: Session, source: models.Source, assignments: List[schemas.SourceAssignmentInput]) -> None:
    existing = {assignment.operator_id: assignment for assignment in source.assignments}
    desired_ids = set()

    for assignment_input in assignments:
        _ensure_operator_exists(db, assignment_input.operator_id)
        desired_ids.add(assignment_input.operator_id)

        if assignment_input.operator_id in existing:
            existing_assignment = existing[assignment_input.operator_id]
            existing_assignment.weight = assignment_input.weight
        else:
            source.assignments.append(
                models.SourceOperatorAssignment(
                    operator_id=assignment_input.operator_id, weight=assignment_input.weight
                )
            )

    for assignment in list(source.assignments):
        if assignment.operator_id not in desired_ids:
            source.assignments.remove(assignment)


def _to_source_read(source: models.Source) -> schemas.SourceRead:
    assignments = [
        schemas.SourceAssignmentRead(
            operator_id=assignment.operator_id,
            operator_name=assignment.operator.name if assignment.operator else "",
            weight=assignment.weight,
        )
        for assignment in sorted(source.assignments, key=lambda item: item.operator_id)
    ]
    return schemas.SourceRead(
        id=source.id,
        name=source.name,
        description=source.description,
        created_at=source.created_at,
        assignments=assignments,
    )


@router.post("/", response_model=schemas.SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: schemas.SourceCreate, db: Session = Depends(get_session)) -> schemas.SourceRead:
    source = models.Source(name=payload.name, description=payload.description)
    db.add(source)
    db.flush()

    if payload.assignments:
        _apply_assignments(db, source, list(payload.assignments))

    db.commit()
    db.refresh(source)
    return _to_source_read(source)


@router.get("/", response_model=List[schemas.SourceRead])
def list_sources(db: Session = Depends(get_session)) -> List[schemas.SourceRead]:
    sources = (
        db.query(models.Source)
        .options(joinedload(models.Source.assignments).joinedload(models.SourceOperatorAssignment.operator))
        .order_by(models.Source.id)
        .all()
    )
    return [_to_source_read(source) for source in sources]


@router.patch("/{source_id}", response_model=schemas.SourceRead)
def update_source(
    source_id: int, payload: schemas.SourceUpdate, db: Session = Depends(get_session)
) -> schemas.SourceRead:
    source = _get_source(db, source_id)

    update_data = payload.dict(exclude_unset=True, exclude={"assignments"})
    for key, value in update_data.items():
        setattr(source, key, value)

    if payload.assignments is not None:
        _apply_assignments(db, source, list(payload.assignments))

    db.add(source)
    db.commit()
    db.refresh(source)

    source = _get_source(db, source_id)
    return _to_source_read(source)


