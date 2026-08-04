from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from backend.app.auth.jwt_handler import decode_access_token
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """FastAPI dependency to extract JWT payload and yield current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("user_id")
    if user_id is None:
        raise credentials_exception
        
    user = await UserRepository.get_by_id(user_id)
    if user is None:
        raise credentials_exception
        
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    # Standardize MongoDB document mapping to UserResponse pydantic model
    # Convert ObjectId to string
    user["id"] = str(user["_id"])
    user["organization_id"] = str(user["organization_id"])
    
    # Fetch Organization Name
    try:
        from backend.app.repositories.organization_repository import OrganizationRepository
        org = await OrganizationRepository.get_by_id(user["organization_id"])
        if org:
            user["organization_name"] = org.get("name", "ForenSight Security")
    except Exception:
        user["organization_name"] = "ForenSight Security"

    return UserResponse(**user)
