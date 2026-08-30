from .api import ApiRouter 
from .main_page import MainPageRouter
from .partials import ParticalPageRouter
from .compress import CompressRouter

__all__ = [
    "ApiRouter",
    "MainPageRouter",
    "ParticalPageRouter",
    "CompressRouter",
]