import asyncio
import secrets
from datetime import datetime
from bson import ObjectId
from backend.app.db.mongodb import db_client
from backend.app.auth.password import hash_password
from backend.app.repositories.password_reset_repository import PasswordResetRepository
from backend.app.services.email_service import EmailService
from backend.app.config import settings

async def main():

    print("=== FORENSIGHT RESET EMAIL DISPATCHER ===")
    target_email = "shleshdarji317@gmail.com"
    
    # 1. Check or Create User in MongoDB
    user = await db_client.db["users"].find_one({"email": target_email})
    if not user:
        print(f"[!] User '{target_email}' not found in MongoDB. Creating user account now...")
        
        # Check or Create Org
        org = await db_client.db["organizations"].find_one({})
        if not org:
            org_res = await db_client.db["organizations"].insert_one({
                "name": "Default Cyber Agency",
                "code": "CYBER-01",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            org_id = org_res.inserted_id
        else:
            org_id = org["_id"]

        now = datetime.utcnow()
        user_dict = {
            "email": target_email,
            "username": "shlesh_investigator",
            "organization_id": org_id,
            "role": "admin",
            "hashed_password": hash_password("Password@123"),
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        res = await db_client.db["users"].insert_one(user_dict)
        user_dict["_id"] = res.inserted_id
        user = user_dict
        print(f"[✓] Account '{target_email}' created successfully in MongoDB!")

    # 2. Generate Reset Token
    reset_token = secrets.token_urlsafe(32)
    user_id_str = str(user["_id"])

    # 3. Store in MongoDB password_resets collection
    await PasswordResetRepository.create_reset_token(
        user_id=user_id_str,
        token=reset_token,
        expires_in_minutes=15
    )
    print(f"[✓] Password reset token generated and saved in MongoDB.")

    # 4. Dispatch Email via Brevo API
    print(f"[*] Sending email to '{target_email}' via Brevo API...")
    sent = await EmailService.send_password_reset_email(
        to_email=target_email,
        username=user.get("username", "Shlesh"),
        reset_token=reset_token
    )

    if sent:
        print(f"[SUCCESS] Email successfully sent to {target_email}!")
        print(f"Reset Link: {settings.FRONTEND_URL}/reset-password?token={reset_token}")
    else:
        print(f"[ERROR] Email dispatch failed. Check API key and sender config.")

if __name__ == "__main__":
    asyncio.run(main())

