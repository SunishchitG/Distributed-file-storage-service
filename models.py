from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class FileRead(BaseModel):
    id: int
    filename: str
    size: int
    upload_time: str
    version: int
    is_public: bool
    user_id: int

    class Config:
        orm_mode = True
