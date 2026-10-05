"""Stand-in for KOMPAS's ksapi.py so CI can test run.py without KOMPAS: no KOMPAS is ever running."""
from constants import constants  # noqa: F401  (the real ksapi.py imports it the same way)


def GetKompas():
    return None
