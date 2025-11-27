from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models


@dataclass
class AllocationResult:
    operator: Optional[models.Operator]
    reason: Optional[str] = None


def compute_operator_loads(session: Session, operator_ids: list[int]) -> dict[int, int]:
    if not operator_ids:
        return {}

    query = (
        select(models.Contact.operator_id, func.count(models.Contact.id))
        .where(
            models.Contact.operator_id.in_(operator_ids),
            models.Contact.status == "active",
        )
        .group_by(models.Contact.operator_id)
    )
    result = session.execute(query)
    return {operator_id: count for operator_id, count in result.all()}


def choose_operator_for_source(session: Session, source: models.Source) -> AllocationResult:
    assignments = [
        assignment
        for assignment in source.assignments
        if assignment.operator is not None and assignment.operator.active
    ]

    if not assignments:
        return AllocationResult(operator=None, reason="No active operators configured for this source")

    operator_ids = [assignment.operator_id for assignment in assignments]
    loads = compute_operator_loads(session, operator_ids)

    eligible = []
    for assignment in assignments:
        operator = assignment.operator
        current_load = loads.get(operator.id, 0)
        limit = operator.load_limit or float("inf")
        if current_load < limit:
            eligible.append((operator, assignment.weight))

    if not eligible:
        return AllocationResult(operator=None, reason="All operators reached their load limit")

    operators, weights = zip(*eligible)
    chosen = random.choices(operators, weights=weights, k=1)[0]
    return AllocationResult(operator=chosen)


