from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token, UserUpdate
from app.security import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ja cadastrado"
        )

    if user_data.cpf:
        existing_cpf = db.query(User).filter(User.cpf == user_data.cpf).first()
        if existing_cpf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF ja cadastrado"
            )

    if user_data.cnpj:
        existing_cnpj = db.query(User).filter(User.cnpj == user_data.cnpj).first()
        if existing_cnpj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ ja cadastrado"
            )

    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        person_type=user_data.person_type,
        cpf=user_data.cpf,
        cnpj=user_data.cnpj,
        phone=user_data.phone,
        cep=user_data.cep,
        street=user_data.street,
        number=user_data.number,
        complement=user_data.complement,
        neighborhood=user_data.neighborhood,
        city=user_data.city,
        state=user_data.state
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desativado"
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout():
    return {"message": "Logout realizado com sucesso"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(user_data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_data.name is not None:
        current_user.name = user_data.name
    if user_data.phone is not None:
        current_user.phone = user_data.phone
    if user_data.person_type is not None:
        current_user.person_type = user_data.person_type
    if user_data.cpf is not None:
        current_user.cpf = user_data.cpf
    if user_data.cnpj is not None:
        current_user.cnpj = user_data.cnpj
    if user_data.cep is not None:
        current_user.cep = user_data.cep
    if user_data.street is not None:
        current_user.street = user_data.street
    if user_data.number is not None:
        current_user.number = user_data.number
    if user_data.complement is not None:
        current_user.complement = user_data.complement
    if user_data.neighborhood is not None:
        current_user.neighborhood = user_data.neighborhood
    if user_data.city is not None:
        current_user.city = user_data.city
    if user_data.state is not None:
        current_user.state = user_data.state

    db.commit()
    db.refresh(current_user)

    return current_user
