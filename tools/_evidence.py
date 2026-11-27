"""Bind local evaluation reports to implementation inputs without a commit cycle."""
import hashlib
from pathlib import Path


def source_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    paths = [root / name for name in ("Cargo.toml", "Cargo.lock", "pyproject.toml", "uv.lock")]
    paths.extend(root / "docs/spec/vectors" / name for name in ("cases.json", "coverage-map.json"))
    for folder in ("crates", "python", "tests", "tools"):
        paths.extend(path for path in (root / folder).rglob("*")
                     if path.suffix in {".rs", ".py", ".toml"})
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}
