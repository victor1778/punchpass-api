from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class Event:
    id: int = None
    status: str = None
    url: str = None
    title: str = None
    location: str = None
    instructor: str = None
    start: dict[str, str] = None
    end: dict[str, str] = None
    timestamp: str = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)
