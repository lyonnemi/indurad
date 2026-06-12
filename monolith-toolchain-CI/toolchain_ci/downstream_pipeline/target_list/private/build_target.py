import dataclasses
from typing import Dict, Optional


@dataclasses.dataclass(frozen=True)
class BuildTarget:
    """CMake build target"""

    target_type: str
    target_language: str
    library_type: Optional[str] = None

    def as_dict(self) -> Dict:
        base_dict = {"target_type": self.target_type, "target_language": self.target_language}
        is_library = self.target_type == "LIBRARY"
        return base_dict | {"library_type": self.library_type} if is_library else base_dict
