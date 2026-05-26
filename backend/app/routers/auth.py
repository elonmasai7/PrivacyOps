import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import AuthChallenge, OAuthIdentity, User
from app.schemas import (
    LoginChallengeResponse,
    MFASetupBeginResponse,
    MFASetupConfirmRequest,
    MFALoginVerifyRequest,
    OAuthCallbackRequest,
    OAuthStartResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.security import create_access_token, hash_password, verify_password
from app.services import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])


def _mfa_challenge(user_id: str, db: Session) -> LoginChallengeResponse:
    challenge_token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=10)
    challenge = AuthChallenge(
        user_id=user_id,
        challenge_type="totp",
        challenge_token=challenge_token,
        expires_at=expires,
    )
    db.add(challenge)
    db.commit()
    return LoginChallengeResponse(
        challenge_token=challenge_token,
        expires_in_seconds=600,
    )


def _google_configured() -> bool:
    return bool(settings.oauth_google_client_id and settings.oauth_google_client_secret and settings.oauth_google_redirect_uri)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.mfa_enabled:
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=_mfa_challenge(user.id, db).model_dump())

    token = create_access_token(subject=user.id)
    write_audit_log(
        db,
        organization_id=None,
        actor_user_id=user.id,
        action="auth.login",
        target_type="user",
        target_id=user.id,
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/mfa/verify-login", response_model=TokenResponse)
def verify_mfa_login(payload: MFALoginVerifyRequest, db: Session = Depends(get_db)):
    challenge = (
        db.query(AuthChallenge)
        .filter(AuthChallenge.challenge_token == payload.challenge_token, AuthChallenge.consumed_at.is_(None))
        .first()
    )
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    if challenge.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Challenge expired")

    user = db.get(User, challenge.user_id)
    if not user or not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not configured")

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(payload.mfa_code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    challenge.consumed_at = datetime.utcnow()
    db.add(challenge)
    db.commit()

    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token)


@router.post("/mfa/setup/begin", response_model=MFASetupBeginResponse)
def begin_mfa_setup(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = pyotp.random_base32()
    user.mfa_temp_secret = secret
    db.add(user)
    db.commit()

    app_name = "PrivacyOps Africa"
    otp_auth_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=app_name)
    return MFASetupBeginResponse(otp_auth_uri=otp_auth_uri, manual_key=secret, app_name=app_name)


@router.post("/mfa/setup/confirm")
def confirm_mfa_setup(
    payload: MFASetupConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.mfa_temp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA setup not initiated")

    totp = pyotp.TOTP(user.mfa_temp_secret)
    if not totp.verify(payload.mfa_code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    user.mfa_secret = user.mfa_temp_secret
    user.mfa_temp_secret = None
    user.mfa_enabled = True
    db.add(user)
    db.commit()
    return {"mfa_enabled": True}


@router.get("/oauth/providers", response_model=list[OAuthStartResponse])
def oauth_providers():
    if _google_configured():
        return [OAuthStartResponse(provider="google", authorization_url=None, status="configured")]
    return [
        OAuthStartResponse(
            provider="google",
            authorization_url=None,
            status="not_configured",
            setup_instructions=(
                "Set OAUTH_GOOGLE_CLIENT_ID, OAUTH_GOOGLE_CLIENT_SECRET, and OAUTH_GOOGLE_REDIRECT_URI "
                "to enable real Google OAuth login."
            ),
        )
    ]


@router.get("/oauth/google/start", response_model=OAuthStartResponse)
def oauth_google_start(state: str | None = None):
    if not _google_configured():
        return OAuthStartResponse(
            provider="google",
            authorization_url=None,
            status="not_configured",
            setup_instructions=(
                "Set OAUTH_GOOGLE_CLIENT_ID, OAUTH_GOOGLE_CLIENT_SECRET, and OAUTH_GOOGLE_REDIRECT_URI "
                "to enable real Google OAuth login."
            ),
        )

    oauth_state = state or secrets.token_urlsafe(24)
    params = {
        "client_id": settings.oauth_google_client_id,
        "redirect_uri": settings.oauth_google_redirect_uri,
        "response_type": "code",
        "scope": settings.oauth_google_scopes,
        "state": oauth_state,
        "access_type": "offline",
        "prompt": "consent",
    }
    authorization_url = f"{settings.oauth_google_authorize_url}?{urlencode(params)}"
    return OAuthStartResponse(provider="google", authorization_url=authorization_url, status="configured")


@router.post("/oauth/callback")
async def oauth_callback(payload: OAuthCallbackRequest, db: Session = Depends(get_db)):
    if payload.provider != "google":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only google provider is supported")
    if not _google_configured():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google OAuth is not configured")

    redirect_uri = payload.redirect_uri or settings.oauth_google_redirect_uri
    token_payload = {
        "code": payload.code,
        "client_id": settings.oauth_google_client_id,
        "client_secret": settings.oauth_google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(settings.oauth_google_token_url, data=token_payload)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="OAuth token exchange failed")
        access_token = token_resp.json().get("access_token")

        userinfo_resp = await client.get(
            settings.oauth_google_userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="OAuth userinfo request failed")
        profile = userinfo_resp.json()

    provider_subject = profile.get("sub")
    email = profile.get("email")
    full_name = profile.get("name") or email
    if not provider_subject or not email:
        raise HTTPException(status_code=422, detail="OAuth response missing required identity fields")

    identity = (
        db.query(OAuthIdentity)
        .filter(OAuthIdentity.provider == "google", OAuthIdentity.provider_subject == provider_subject)
        .first()
    )
    user = None
    if identity:
        user = db.get(User, identity.user_id)
        identity.last_login_at = datetime.utcnow()
        db.add(identity)
    else:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            user = User(
                email=email.lower(),
                full_name=full_name,
                password_hash=hash_password(secrets.token_urlsafe(32)),
            )
            db.add(user)
            db.flush()
        identity = OAuthIdentity(
            user_id=user.id,
            provider="google",
            provider_subject=provider_subject,
            email=email.lower(),
        )
        db.add(identity)

    db.commit()

    if user.mfa_enabled:
        return _mfa_challenge(user.id, db)

    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token)
