from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserLogin, Token, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # SECURITY: public self-registration must only ever be able to create a
    # CITIZEN account. health_official/admin accounts carry access to
    # government dashboards and aggregate public-health data, so they must
    # be provisioned out-of-band (demo seed script / an authenticated admin
    # action) rather than through this open endpoint. Any attempt to
    # self-register a privileged role is explicitly rejected rather than
    # silently downgraded, so the caller gets a clear signal.
    if payload.role != UserRole.citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration can only create citizen accounts. "
                   "Health official / admin accounts are provisioned separately.",
        )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.citizen,
        preferred_language=payload.preferred_language,
        district=payload.district,
        state=payload.state,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
