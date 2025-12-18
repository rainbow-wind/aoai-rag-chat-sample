from pydantic import BaseModel

class DocumentStructure(BaseModel):
    content: str
    keywords: list[str]
    is_contain_image: bool