from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.schemas.user import UserCreate, UserResponse, UserUpdate, Token, UserRole
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.auth.password import hash_password, verify_password
from backend.app.auth.jwt_handler import create_access_token
from backend.app.auth.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate):
    """Register a new user. Role defaults to 'investigator'. Admin role requires an existing admin to set it."""
    if not ObjectId.is_valid(payload.organization_id):
        raise HTTPException(status_code=400, detail="Invalid organization ID format")

    org = await OrganizationRepository.get_by_id(payload.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing_user = await UserRepository.get_by_email(payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email address already registered")

    # Prevent self-assigned admin role on registration — default to investigator
    safe_role = payload.role if payload.role.value != "admin" else UserRole.INVESTIGATOR

    now = datetime.utcnow()
    user_dict = {
        "email": payload.email,
        "username": payload.username,
        "organization_id": ObjectId(payload.organization_id),
        "role": safe_role.value,
        "hashed_password": hash_password(payload.password),
        "is_active": payload.is_active,
        "created_at": now,
        "updated_at": now,
    }

    created_user = await UserRepository.create(user_dict)
    created_user["id"] = str(created_user["_id"])
    created_user["organization_id"] = str(created_user["organization_id"])
    return created_user

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate credentials and return a JWT access token."""
    # Note: oauth2 password form uses username field for credentials (which is our email)
    user = await UserRepository.get_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    # Create JWT access token
    token_data = {
        "user_id": str(user["_id"]),
        "organization_id": str(user["organization_id"]),
        "role": user["role"]
    }
    
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Retrieve logged-in user profile details."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update the logged-in user's profile (username, email, password)."""
    update_fields: dict = {"updated_at": datetime.utcnow()}

    if payload.username is not None:
        update_fields["username"] = payload.username

    if payload.email is not None:
        # Ensure new email is not taken by another account
        existing = await UserRepository.get_by_email(payload.email)
        if existing and str(existing["_id"]) != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already in use by another account.",
            )
        update_fields["email"] = payload.email

    if payload.password is not None:
        update_fields["hashed_password"] = hash_password(payload.password)

    if len(update_fields) == 1:  # only updated_at — nothing to do
        return current_user

    updated = await UserRepository.update(current_user.id, update_fields)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile.",
        )

    updated["id"] = str(updated["_id"])
    updated["organization_id"] = str(updated["organization_id"])
    return UserResponse(**updated)
