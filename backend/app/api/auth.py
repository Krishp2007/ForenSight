from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.schemas.user import UserCreate, UserResponse, Token
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.auth.password import hash_password, verify_password
from backend.app.auth.jwt_handler import create_access_token
from backend.app.auth.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate):
    """Register a new investigator user within an organization."""
    # 1. Verify organization exists
    if not ObjectId.is_valid(payload.organization_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
        
    org = await OrganizationRepository.get_by_id(payload.organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
        
    # 2. Check if user already exists
    existing_user = await UserRepository.get_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )
        
    # 3. Hash password and insert
    now = datetime.utcnow()
    hashed_pwd = hash_password(payload.password)
    
    user_dict = {
        "email": payload.email,
        "username": payload.username,
        "organization_id": ObjectId(payload.organization_id),
        "role": payload.role.value,
        "hashed_password": hashed_pwd,
        "is_active": payload.is_active,
        "created_at": now,
        "updated_at": now
    }
    
    created_user = await UserRepository.create(user_dict)
    
    # Map MongoDB document to UserResponse
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
