from typing import List
from fastapi import HTTPException, status
from backend.app.schemas.user import UserRole

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user_role: str) -> bool:
        """Verify if current user role is in the allowed roles list."""
        if user_role not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have sufficient permissions to perform this action"
            )
        return True

# Predefined role checking helper constraints
require_admin = RoleChecker([UserRole.ADMIN])
require_investigator = RoleChecker([UserRole.ADMIN, UserRole.INVESTIGATOR])
require_viewer = RoleChecker([UserRole.ADMIN, UserRole.INVESTIGATOR, UserRole.VIEWER])
