from dataclasses import asdict, dataclass


@dataclass
class User:
    id: int = None
    first_name: str = None
    last_name: str = None
    phone: str = None
    email: str = None

    def to_dict(self) -> dict:
        return asdict(self)
