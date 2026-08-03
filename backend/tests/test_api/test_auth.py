import sys
import os
from datetime import timedelta

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.auth.password import hash_password, verify_password
from backend.app.auth.jwt_handler import create_access_token, decode_access_token

def test_password_hashing():
    print("Testing password hashing...")
    pwd = "MySuperSecretPassword"
    hashed = hash_password(pwd)
    
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    print("[OK] Password hashing verified successfully!")

def test_jwt_tokens():
    print("\nTesting JWT tokens...")
    user_payload = {
        "user_id": "60c72b2f9b1d8b2a5c8b4568",
        "organization_id": "60c72b2f9b1d8b2a5c8b4567",
        "role": "investigator"
    }
    
    token = create_access_token(user_payload, expires_delta=timedelta(minutes=5))
    assert isinstance(token, str)
    print(f"[OK] Token generated: {token[:30]}...")
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["user_id"] == user_payload["user_id"]
    assert decoded["organization_id"] == user_payload["organization_id"]
    assert decoded["role"] == user_payload["role"]
    print("[OK] Token decoded and verified successfully!")

    # Test invalid token
    assert decode_access_token("invalid.token.here") is None
    print("[OK] Invalid token safety check passed!")

if __name__ == "__main__":
    print("Starting local auth unit tests...")
    try:
        test_password_hashing()
        test_jwt_tokens()
        print("\nALL AUTHENTICATION INTEGRATION CHECKS PASSED PERFECTLY!")
    except Exception as e:
        print(f"\nAuth tests failed: {e}")
