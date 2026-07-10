from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass(frozen=True)
class FileRecord:
    rel_path: str
    abs_path: str
    name: str
    extension: str
    size_bytes: int
    mtime_ns: int
    category: str
    is_binary: bool
    is_sensitive: bool
    default_selected: bool
    selection_reason: str = ""

    @property
    def estimated_tokens(self) -> int:
        """Fast byte-based estimate. Real LLM tokenizers vary by language/model."""
        if self.is_binary:
            return 0
        return max(1, (self.size_bytes + 3) // 4)


@dataclass
class ScanResult:
    root_path: str
    files: List[FileRecord] = field(default_factory=list)
    skipped_dirs: Set[str] = field(default_factory=set)
    scanner_name: str = "filesystem"
    project_types: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SelectionResult:
    selected_paths: Set[str] = field(default_factory=set)
    names_only_paths: Set[str] = field(default_factory=set)
    blocked_sensitive_paths: Set[str] = field(default_factory=set)
    estimated_tokens: int = 0


@dataclass
class RunSummary:
    report_path: Optional[str]
    file_count: int
    content_count: int
    binary_count: int
    names_only_count: int
    estimated_tokens: int
    scanner_name: str
    project_types: List[str]
    warnings: List[str] = field(default_factory=list)
