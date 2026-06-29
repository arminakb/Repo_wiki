from __future__ import annotations

import re


def classify_task(task: str) -> str:
    text = task.lower()
    terms = term_set(task)
    if has_any(text, terms, ("test", "tests", "pytest", "jest", "vitest", "spec", "specs")):
        return "test_generation"
    if has_any(text, terms, ("bug", "fix", "error", "exception", "crash")):
        return "bug_fix"
    if has_any(text, terms, ("refactor", "cleanup", "clean up", "simplify")):
        return "refactor"
    if has_any(text, terms, ("database", "schema", "migration", "sql", "prisma")):
        return "database_change"
    if has_any(text, terms, ("security", "auth", "password", "token", "session")):
        return "security_change"
    if has_any(text, terms, ("api", "endpoint", "route", "controller")):
        return "api_integration"
    if has_any(text, terms, ("component", "page", "ui", "frontend", "react")):
        return "frontend_feature"
    return "backend_feature"


def infer_domain(task: str) -> str | None:
    text = task.lower()
    terms = term_set(task)
    mapping = {
        "auth": ("auth", "login", "password", "token", "session", "user"),
        "api": ("api", "endpoint", "route", "controller"),
        "database": ("database", "schema", "migration", "sql", "prisma"),
        "ui": ("component", "page", "frontend", "react", "view"),
        "testing": ("test", "tests", "pytest", "jest", "spec", "specs"),
        "docs": ("readme", "docs", "documentation"),
    }
    for domain, needles in mapping.items():
        if has_any(text, terms, needles):
            return domain
    return None


def term_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def has_any(text: str, terms: set[str], needles: tuple[str, ...]) -> bool:
    for needle in needles:
        if " " in needle:
            if needle in text:
                return True
            continue
        if needle in terms:
            return True
    return False


def infer_language(task: str) -> str | None:
    text = task.lower()
    if "typescript" in text or "next.js" in text or "nextjs" in text:
        return "TypeScript"
    if "javascript" in text or "node" in text or "express" in text:
        return "JavaScript"
    if "python" in text or "fastapi" in text or "django" in text or "flask" in text:
        return "Python"
    return None


def infer_framework(task: str) -> str | None:
    text = task.lower()
    frameworks = {
        "Next.js": ("next.js", "nextjs"),
        "React": ("react",),
        "FastAPI": ("fastapi",),
        "Django": ("django",),
        "Flask": ("flask",),
        "Prisma": ("prisma",),
        "Express": ("express",),
    }
    for framework, needles in frameworks.items():
        if any(needle in text for needle in needles):
            return framework
    return None
