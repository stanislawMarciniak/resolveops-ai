from enum import StrEnum


class AccountStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class InvoiceStatus(StrEnum):
    OPEN = "OPEN"
    OVERDUE = "OVERDUE"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    RECEIVED = "RECEIVED"
    MATCHED = "MATCHED"
    REVERSED = "REVERSED"


class Currency(StrEnum):
    PLN = "PLN"
    EUR = "EUR"
    USD = "USD"


class EvidenceSource(StrEnum):
    CRM = "CRM"
    BILLING = "BILLING"
    POLICY = "POLICY"
    USER = "USER"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ApprovalDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ExecutionStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class ReviewVerdict(StrEnum):
    APPROVE = "APPROVE"
    REVISE = "REVISE"
    ESCALATE = "ESCALATE"