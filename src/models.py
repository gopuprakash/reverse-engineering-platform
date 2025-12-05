from dataclasses import dataclass

@dataclass
class CodebaseMetadata:
    id: str
    name: str
    source: str
    language: str
    priority: int = 5
    entry_points: list = None

    def __post_init__(self):
        if self.entry_points is None:
            self.entry_points = []
