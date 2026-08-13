import pytest
from app.agents.reviewer import (
    ReviewerResult,
    to_plan_review,
)
from app.models import ReviewVerdict
from pydantic import ValidationError


def test_revise_requires_feedback() -> None:
    with pytest.raises(
        ValidationError
    ):
        ReviewerResult(
            verdict=(
                ReviewVerdict.REVISE
            ),
            summary=(
                "Plan needs changes."
            ),
            issues=[
                "Wrong action order."
            ],
        )


def test_reviewer_result_becomes_domain_model() -> None:
    result = ReviewerResult(
        verdict=(
            ReviewVerdict.APPROVE
        ),
        summary=(
            "Plan is evidence-grounded "
            "and policy-compliant."
        ),
        issues=[],
    )

    review = to_plan_review(
        result
    )

    assert (
        review.verdict
        is ReviewVerdict.APPROVE
    )

    assert review.issues == []

    assert (
        review.revision_feedback
        is None
    )