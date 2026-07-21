from typing import Optional

from pydantic import BaseModel


class GenerateDetailDesignInput(BaseModel):
    project_id: str
    job_id: str
    basic_design: str
    ui_design: Optional[str] = None
