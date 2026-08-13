from enum import StrEnum

from pydantic import BaseModel


class UserRole(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"


class AuthenticatedUser(BaseModel):
    subject: str
    email: str
    role: UserRole