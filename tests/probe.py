"""Checks the environment run.py gives a script. CI runs it against tests/stub:

    KOMPAS_BOX=none KOMPAS_DIR=tests/stub python3 skill/kompas-3d/scripts/run.py tests/probe.py один "два слова"
"""
import os
import sys

import ksapi
from constants import constants as c

assert sys.argv[1:] == ['один', 'два слова'], sys.argv
assert os.path.basename(os.getcwd()) == 'Bin', os.getcwd()
assert ksapi.GetKompas() is None and c.ksDocumentFragment == 2
try:
    import ks  # noqa: F401
except SystemExit as e:                  # ks finds the skill scripts and stops: no KOMPAS running
    assert 'KOMPAS not found' in str(e), e
else:
    raise AssertionError('ks imported without a KOMPAS')
print('probe ok: чертёж')
