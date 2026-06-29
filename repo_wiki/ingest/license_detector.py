from __future__ import annotations

from pathlib import Path

from repo_wiki.domain.errors import LicensePolicyViolation


PERMISSIVE_LICENSES = {
    "mit": "MIT",
    "apache": "Apache-2.0",
    "bsd": "BSD",
    "isc": "ISC",
}

LICENSE_POLICIES = {
    "allow_all_public",
    "metadata_only",
    "permissive_only",
    "private_local_only",
}


def detect_license(root: Path) -> str | None:
    for candidate in root.iterdir():
        if candidate.is_file() and candidate.name.lower().startswith(("license", "copying")):
            text = candidate.read_text(encoding="utf-8", errors="ignore").lower()
            for needle, label in PERMISSIVE_LICENSES.items():
                if needle in text:
                    return label
            if "gpl" in text:
                return "GPL"
            return "custom"
    return None


def snippet_allowed(license_name: str | None, policy: str) -> bool:
    validate_license_policy(policy)
    if policy == "allow_all_public":
        return True
    if policy == "metadata_only":
        return False
    if policy == "private_local_only":
        return False
    if policy == "permissive_only":
        return license_name in {"MIT", "Apache-2.0", "BSD", "ISC"}
    return False


def validate_license_policy(policy: str) -> None:
    if policy not in LICENSE_POLICIES:
        raise LicensePolicyViolation(f"unsupported license policy: {policy}")
