"""Chat-related Pydantic schemas."""
from typing import List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionsRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    class Config:
        extra = "allow"
        # 这是用来兜底的，允许额外字段。
        # 这个 Config 不是普通 Python class，它是 Pydantic 的模型配置类。
        # 作用是：控制这个 BaseModel 的行为方式。允许 JSON 里出现“没有在模型里声明的字段”，并且不要报错。
