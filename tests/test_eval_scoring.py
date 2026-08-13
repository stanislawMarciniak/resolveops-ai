from app.evals.scoring import (
    root_cause_score,
)


def test_root_cause_keyword_groups() -> None:
    score = root_cause_score(
        root_cause=(
            "Payment TX-9912 remained "
            "unmatched to invoice INV-8231, "
            "causing the billing hold and "
            "account suspension."
        ),
        keyword_groups=[
            ["TX-9912"],
            ["INV-8231", "INV8231"],
            [
                "unmatched",
                "not matched",
            ],
            [
                "hold",
                "suspension",
            ],
        ],
    )

    assert score == 1.0


def test_partial_root_cause() -> None:
    score = root_cause_score(
        root_cause=(
            "Invoice INV-8231 is overdue."
        ),
        keyword_groups=[
            ["TX-9912"],
            ["INV-8231"],
        ],
    )

    assert score == 0.5


def test_no_ground_truth_returns_none() -> None:
    score = root_cause_score(
        root_cause=None,
        keyword_groups=[],
    )

    assert score is None