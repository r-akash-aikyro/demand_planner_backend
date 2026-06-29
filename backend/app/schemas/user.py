from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str
    full_name: str | None = None
    is_active: bool


class UserCreateIn(BaseModel):
    email: EmailStr
    password: str
    role: str = "viewer"
    full_name: str | None = None


class UserPatchIn(BaseModel):
    role: str | None = None
    full_name: str | None = None


class UserStatusIn(BaseModel):
    is_active: bool
