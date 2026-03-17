from __future__ import annotations

from html import escape

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse

from app.core.auth import (
    clear_session_cookie,
    get_available_plans,
    get_optional_current_user,
    issue_session_cookie,
    login_user,
    request_password_reset,
    resend_verification_email,
    reset_password,
    serialize_user_session,
    sign_up_user,
    verify_email_token,
)
from app.core.config import settings
from app.core.mail import LocalFileMailProvider, mail_provider
from app.schemas.auth import (
    ActionStatusResponse,
    AuthSessionResponse,
    DevMailMessage,
    ForgotPasswordRequest,
    LoginRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignUpRequest,
    VerifyEmailRequest,
)

router = APIRouter(tags=["auth"])


@router.post("/auth/signup", response_model=AuthSessionResponse)
async def signup(payload: SignUpRequest, response: Response):
    session = sign_up_user(payload.email, payload.password, payload.full_name)
    issue_session_cookie(response, session.user.id)
    return session


@router.post("/auth/login", response_model=AuthSessionResponse)
async def login(payload: LoginRequest, response: Response):
    session = login_user(payload.email, payload.password)
    issue_session_cookie(response, session.user.id)
    return session


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    clear_session_cookie(request, response)
    return {"success": True}


@router.post("/auth/verify-email", response_model=ActionStatusResponse)
async def verify_email(payload: VerifyEmailRequest):
    return verify_email_token(payload.token)


@router.post("/auth/resend-verification", response_model=ActionStatusResponse)
async def resend_verification(
    payload: ResendVerificationRequest,
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    return resend_verification_email(str(payload.email) if payload.email else None, user)


@router.post("/auth/forgot-password", response_model=ActionStatusResponse)
async def forgot_password(payload: ForgotPasswordRequest):
    return request_password_reset(str(payload.email))


@router.post("/auth/reset-password", response_model=ActionStatusResponse)
async def reset_password_route(payload: ResetPasswordRequest):
    return reset_password(payload.token, payload.password)


@router.get("/auth/me", response_model=AuthSessionResponse)
async def me(
    request: Request,
    response: Response,
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    if not user:
        if request.cookies.get(settings.session_cookie_name):
            clear_session_cookie(request, response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please sign in again.",
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return serialize_user_session(user)


@router.get("/auth/plans")
async def plans():
    return {"plans": get_available_plans()}


@router.get("/auth/status")
async def auth_status(user: dict[str, object] | None = Depends(get_optional_current_user)):
    return {
        "authenticated": bool(user),
        "email_verified": bool(user.get("email_verified")) if user else False,
    }


@router.get("/auth/dev/messages/latest", response_model=DevMailMessage)
async def latest_dev_message(email: str = Query(...), kind: str = Query(...)):
    if settings.app_env.lower() == "production" or not isinstance(mail_provider, LocalFileMailProvider):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dev mail preview is not available.")
    message = mail_provider.get_latest_message(email, kind)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching dev message was found.")
    return DevMailMessage.model_validate(message)


@router.get("/auth/dev/messages/{message_id}", response_class=HTMLResponse)
async def dev_message_preview(message_id: str):
    if settings.app_env.lower() == "production" or not isinstance(mail_provider, LocalFileMailProvider):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dev mail preview is not available.")
    message = mail_provider.get_message(message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    subject = escape(str(message.get("subject", "CreatorLab mail preview")))
    to_email = escape(str(message.get("to_email", "")))
    action_url = str(message.get("action_url") or "")
    html_body = str(message.get("html_body") or "")
    action_button = (
        f'<p style="margin-top:24px;"><a href="{escape(action_url)}" '
        'style="display:inline-block;padding:12px 20px;border-radius:999px;'
        'background:#0f766e;color:white;text-decoration:none;">Open action link</a></p>'
        if action_url
        else ""
    )
    return HTMLResponse(
        f"""
        <html>
          <head>
            <title>{subject}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1" />
          </head>
          <body style="font-family:Arial,sans-serif;background:#f4f5f7;padding:32px;color:#0f172a;">
            <div style="max-width:720px;margin:0 auto;background:white;border-radius:24px;padding:32px;box-shadow:0 18px 50px rgba(15,23,42,0.08);">
              <p style="font-size:12px;letter-spacing:0.2em;text-transform:uppercase;color:#0f766e;">CreatorLab dev mail preview</p>
              <h1 style="margin-top:12px;">{subject}</h1>
              <p style="color:#475569;">To: {to_email}</p>
              {action_button}
              <div style="margin-top:24px;padding-top:24px;border-top:1px solid #e2e8f0;">
                {html_body}
              </div>
            </div>
          </body>
        </html>
        """
    )
