from typing import Union
from pydantic import BaseModel

class VM(BaseModel):
    cpu:int
    ram:int
    disk:int