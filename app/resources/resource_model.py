
from dataclasses import dataclass, field
from typing import List

class FromDictMixin:
    @classmethod
    def from_dict(cls, data: dict) -> 'FromDictMixin':
        return cls(**data)

@dataclass
class CustomPyComponent(FromDictMixin):
    name: str
    description: str
    group: str = "features"
    subgroup: str = ""
    values: List[str] = field(default_factory=lambda: ['no', 'yes'])

@dataclass
class CustomPy(FromDictMixin):
    filename: str
    params_list: List[CustomPyComponent] = field(default_factory=list)

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