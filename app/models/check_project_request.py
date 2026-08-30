from pydantic import BaseModel
class CheckProjectRequest(BaseModel):
    folder: str
    html_name: str = "index"