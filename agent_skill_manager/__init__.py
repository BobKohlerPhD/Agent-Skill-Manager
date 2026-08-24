"""Repository-wide quality checks for Agent Skills."""

from .quality import AuditResult, Diagnostic, SkillPackage, audit_repository, discover_skills

__all__ = [
    "AuditResult",
    "Diagnostic",
    "SkillPackage",
    "audit_repository",
    "discover_skills",
]

__version__ = "2.0.0"
