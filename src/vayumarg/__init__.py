"""Vayumarg - AI/ML Decision-Support System for Tropical Cyclones.

Foundational package for SIH 2026 / Team VortexA.
"""

import os

# Ensure Windows Defender Application Control / AppLocker environments
# run smoothly without requiring unsigned compiled C extensions.
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

__version__ = "0.1.0"
