#!/usr/bin/env python3
"""Install Queen helper only in an overlay-matched FEX source component."""
import sys
from pathlib import Path
root=Path(sys.argv[1]); here=Path(__file__).resolve().parent
folder=root/'Source/Windows/ARM64EC'
p=folder/'Module.cpp';s=p.read_text()
anchor='NTSTATUS ProcessInit() {'
assert s.count(anchor)==1
s=s.replace(anchor,'#ifdef FEX_IOS_HOST\n#include "QueenNativeNav.h"\n#endif\n\n'+anchor)
end='  return STATUS_SUCCESS;\n}\n\nvoid ProcessTerm('
assert s.count(end)==1
s=s.replace(end,'#ifdef FEX_IOS_HOST\n  InstallQueenNativeNav(MainModule);\n#endif\n\n'+end)
for name in ['QueenNativeNav.h','QueenNativeNavKernel.h','QueenNativeNavFingerprint.h']:
    dest=folder/name
    assert not dest.exists(),dest
    dest.write_bytes((here/name).read_bytes())
p.write_text(s)
p=folder/'libarm64ecfex.def';s=p.read_text()
assert 'QueenNativeLedgeFilter' not in s
p.write_text(s+'\n  QueenNativeLedgeFilter\n')
print('Queen native ledge-filter startup hook installed; no Module.S/game-file changes')
