import asyncio
import httpx
from backend.app.config import settings

async def test_brevo():
    print("=== BREVO DIAGNOSTIC TEST ===")
    print(f"BREVO_API_KEY: {settings.BREVO_API_KEY[:15]}...")
    print(f"EMAILS_FROM_EMAIL: {settings.EMAILS_FROM_EMAIL}")
    print(f"EMAILS_FROM_NAME: {settings.EMAILS_FROM_NAME}")

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {
            "name": settings.EMAILS_FROM_NAME,
            "email": settings.EMAILS_FROM_EMAIL
        },
        "to": [
            {
                "email": "shleshdarji317@gmail.com",
                "name": "Shlesh"
            }
        ],
        "subject": "ForenSight Brevo Diagnostic Test",
        "htmlContent": "<h3>ForenSight Test Email</h3><p>If you see this, Brevo API is working perfectly!</p>",
        "textContent": "ForenSight Test Email - Brevo API is working!"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_brevo())
