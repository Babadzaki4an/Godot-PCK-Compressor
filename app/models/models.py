from typing import List

from pydantic import BaseModel
class CheckProjectRequest(BaseModel):
    folder: str
    html_name: str = "index"

class CompressRequest(BaseModel):
    folder: str                     
    html_name: str = "index"       
    compression_type: str = "zip"   
    create_backup: bool = True
    wasm_level: int = 9             
    pck_level: int = 9              
    exclude_extensions: List[str] = [] 