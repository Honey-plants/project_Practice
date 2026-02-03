from abc import ABC, abstractmethod
from typing import Optional

class Storage(ABC):
    @abstractmethod
    def put_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> None:
        ...

    @abstractmethod
    def get_bytes(self, key: str) -> bytes:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def delete_prefix(self, prefix: str) -> None:
        """
        prefix 밑으로 전부 삭제(임시 폴더 통째 삭제용)
        """
        ...
