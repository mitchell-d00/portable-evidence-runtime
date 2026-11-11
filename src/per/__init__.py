"""Portable Evidence Runtime: deterministic, local, exact-key reference engine.

No network, third-party libraries, language-model execution, or runtime installation.
"""
from .core import (
    CapsuleError, DEFAULT_POLICY, FORMAT, answer, build_capsule,
    canonical_json, verify_capsule, record_hash, root_hash,
)
__all__ = ['CapsuleError','DEFAULT_POLICY','FORMAT','answer','build_capsule',
           'canonical_json','verify_capsule','record_hash','root_hash']
