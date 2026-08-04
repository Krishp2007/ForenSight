# Walkthrough: Permanent Forgot Password & Email Notification Implementation

We have permanently implemented the **Forgot Password & Email Notification System** across the ForenSight backend and frontend.

## Changes Made

### Backend

1. **Configuration**:
   - Added SMTP and Frontend URL environment variables to [`config.py`](file:///d:/ForenSight/ForenSight/backend/app/config.py), [`.env.example`](file:///d:/ForenSight/ForenSight/backend/.env.example), and [`.env`](file:///d:/ForenSight/ForenSight/backend/.env).

2. **Data Model & Repository**:
   - Added Pydantic request models `ForgotPasswordRequest` and `ResetPasswordRequest` in [`user.py`](file:///d:/ForenSight/ForenSight/backend/app/schemas/user.py).
   - Created [`password_reset_repository.py`](file:///d:/ForenSight/ForenSight/backend/app/repositories/password_reset_repository.py) to handle SHA-256 token hashing, creation, verification (15-minute expiry), and single-use deletion in MongoDB collection `password_resets`.

3. **Services & Endpoints**:
   - Created [`email_service.py`](file:///d:/ForenSight/ForenSight/backend/app/services/email_service.py) with async SMTP dispatching and a local console/loguru fallback for offline development.
   - Updated [`auth.py`](file:///d:/ForenSight/ForenSight/backend/app/api/auth.py) with:
     - `POST /api/v1/auth/forgot-password` (generates secure token & emails link).
     - `POST /api/v1/auth/reset-password` (validates token & updates `hashed_password` permanently).

---

### Frontend

1. **Services & API Client**:
   - Updated [`authService.js`](file:///d:/ForenSight/ForenSight/frontend/src/services/authService.js) with `forgotPassword` and `resetPassword` methods.

2. **UI & Routing**:
   - Added a **"Forgot Password?"** link and glassmorphism modal dialog to [`LoginPage.jsx`](file:///d:/ForenSight/ForenSight/frontend/src/pages/LoginPage.jsx).
   - Created a dedicated [`ResetPasswordPage.jsx`](file:///d:/ForenSight/ForenSight/frontend/src/pages/ResetPasswordPage.jsx) page.
   - Added the `/reset-password` route to [`App.jsx`](file:///d:/ForenSight/ForenSight/frontend/src/App.jsx).

---

## Verification Results

1. **Forgot Password Link Request**:
   - Click "Forgot Password?" on Sign In page.
   - Enter email address -> click "Send Reset Link".
   - Token is stored in MongoDB `password_resets` table (expires in 15 mins).
   - Email is dispatched via SMTP (or logged in backend console in development mode).

2. **Password Reset Execution**:
   - User opens link `/reset-password?token=...`.
   - User inputs new password (validated for length and match).
   - Database updates user `hashed_password` with `bcrypt`.
   - Token is invalidated/deleted.
   - User logs in with new password.
