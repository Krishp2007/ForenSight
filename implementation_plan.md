# SMS Password Reset Link Implementation Plan

This plan outlines adding **SMS-based Password Reset Links** to ForenSight alongside Email reset links, allowing investigators to enter their Mobile Phone Number to receive a reset link via SMS.

## User Review Required

> [!IMPORTANT]
> **SMS Provider Options**:
> 1. **Brevo Transactional SMS API** (Uses your existing Brevo API key: `https://api.brevo.com/v3/transactionalSMS/send`).
> 2. **Twilio SMS API** (Requires `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`).
> 3. **Fast2SMS / TextLocal** (Popular for Indian mobile numbers `+91`).
> 
> *Note*: For real SMS delivery to phones, SMS credits or sender ID registration (e.g. DLT registration in India) are required by telecom regulations. In local development mode, if SMS fails or credits are missing, the SMS reset link will automatically log to the backend console terminal so you can test smoothly!

---

## Proposed Changes

### Backend Configuration & Models

#### [MODIFY] [`config.py`](file:///d:/ForenSight/ForenSight/backend/app/config.py)
- Add SMS configuration variables (`SMS_PROVIDER`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`).

#### [MODIFY] [`user.py` schema](file:///d:/ForenSight/ForenSight/backend/app/schemas/user.py)
- Add `phone_number` field (e.g., `+919876543210`) to `UserBase`, `UserCreate`, `UserUpdate`, and `ForgotPasswordRequest`.

#### [MODIFY] [`user_repository.py`](file:///d:/ForenSight/ForenSight/backend/app/repositories/user_repository.py)
- Add `get_by_phone(phone_number)` to query user accounts by phone number.

---

### Backend Services & API Endpoints

#### [NEW] [`sms_service.py`](file:///d:/ForenSight/ForenSight/backend/app/services/sms_service.py)
- Asynchronous SMS dispatcher supporting Brevo Transactional SMS API, Twilio, and console log fallback.

#### [MODIFY] [`auth.py`](file:///d:/ForenSight/ForenSight/backend/app/api/auth.py)
- Update `POST /api/v1/auth/forgot-password` to accept `email_or_phone`.
- Lookup user by email OR phone number.
- If phone number is matched, send SMS via `SmsService`.
- If email is matched, send Email via `EmailService`.

---

### Frontend Components & UI

#### [MODIFY] [`LoginPage.jsx`](file:///d:/ForenSight/ForenSight/frontend/src/pages/LoginPage.jsx)
- Update "Forgot Password" modal input label to **"Email Address or Mobile Number"**.
- Allow users to enter e.g. `+919876543210` or `user@gmail.com`.

#### [MODIFY] [`RegisterPage.jsx`](file:///d:/ForenSight/ForenSight/frontend/src/pages/RegisterPage.jsx)
- Add **"Mobile Phone Number"** input field (e.g. `+919876543210`) so new users can save their mobile number to their profile.

---

## Verification Plan

### Manual Verification
1. Register a user account with a Mobile Phone Number (`+919876543210`).
2. Go to `/login` -> Click "Forgot Password?".
3. Type the mobile phone number (`+919876543210`).
4. Backend generates the reset token and triggers SMS delivery (or logs the SMS reset URL to the terminal in dev fallback mode).
5. Open the reset link in mobile browser `/reset-password?token=...` and verify password update.
