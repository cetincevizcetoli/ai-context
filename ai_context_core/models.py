from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


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


@dataclass(frozen=True)
class StructureEntry:
    """A lightweight project-map entry discovered without reading file contents."""

    rel_path: str
    name: str
    kind: str  # "dir" or "file"
    is_pruned: bool = False
    reason: str = ""
    immediate_file_count: int = 0
    immediate_dir_count: int = 0
    count_capped: bool = False
    size_bytes: int = 0
    is_sensitive: bool = False


@dataclass
class ScanResult:
    root_path: str
    files: List[FileRecord] = field(default_factory=list)
    structure_entries: List[StructureEntry] = field(default_factory=list)
    skipped_dirs: Set[str] = field(default_factory=set)
    scanner_name: str = "filesystem"
    project_types: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SelectionResult:
    # Paths whose content is eligible to be written to the report.
    selected_paths: Set[str] = field(default_factory=set)
    # Selected files demoted to name-only because of the token budget.
    names_only_paths: Set[str] = field(default_factory=set)
    blocked_sensitive_paths: Set[str] = field(default_factory=set)
    estimated_tokens: int = 0

    # Project map controls. These may include files not selected for content.
    map_file_paths: Set[str] = field(default_factory=set)
    map_dir_paths: Set[str] = field(default_factory=set)
    summary_dirs: Set[str] = field(default_factory=set)
    hidden_dirs: Set[str] = field(default_factory=set)
    path_notes: Dict[str, str] = field(default_factory=dict)
    folder_modes: Dict[str, str] = field(default_factory=dict)
    omitted_map_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class RunSummary:
    report_path: Optional[str]
    file_count: int
    content_count: int
    binary_count: int
    names_only_count: int
    map_file_count: int
    estimated_tokens: int
    scanner_name: str
    project_types: List[str]
    warnings: List[str] = field(default_factory=list)
