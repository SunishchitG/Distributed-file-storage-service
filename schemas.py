from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

class FileRead(BaseModel):
    id: int
    filename: str
    size: int
    upload_time: str
    user_id: int

    class Config:
        orm_mode = True
