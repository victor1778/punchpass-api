from dataclasses import asdict, dataclass

@dataclass
class ScheduleItem:
    id: str = None
    status: str = None
    url: str = None
    title: str = None
    location: str = None
    instructor: str = None
    start: dict[str, str] = None
    end: dict[str, str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# @dataclass
# class User:
#     id: str = None
#     first_name: str = None
#     last_name: str = None
#     phone: str = None
#     email: str = None

#     def to_dict(self) -> dict:
#         return asdict(self)
