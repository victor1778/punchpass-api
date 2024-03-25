from pydantic import BaseModel, Field

class User(BaseModel):
    id: int = Field(examples=[12345678])
    first_name: str = Field(examples=["John"])
    last_name: str = Field(examples=["Doe"])
    phone: str = Field(examples=["1234567890"])
    email: str = Field(examples=["johndoe@example.com"])


class ReadUser(BaseModel):
    email: str = Field(examples=["johndoe@example.com"])