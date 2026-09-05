
from dataclasses import dataclass

class FromDictMixin:
    @classmethod
    def from_dict(cls, data: dict) -> 'FromDictMixin':
        instance = cls.__new__(cls)
        for key, value in data.items():
            setattr(instance, key, value)

        return instance

@dataclass
class ChangeResource(FromDictMixin):
    change: str
    to: str

@dataclass
class InsertAfter(FromDictMixin):
    find: str
    insert: str

@dataclass
class PlatformSDKData(FromDictMixin):
    sdk_script: str
    sdk_init: str