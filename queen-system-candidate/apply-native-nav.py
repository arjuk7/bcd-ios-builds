#!/usr/bin/env python3
"""Install Queen helper only in an overlay-matched FEX source component."""
import sys
from pathlib import Path
root=Path(sys.argv[1]); here=Path(__file__).resolve().parent
folder=root/'Source/Windows/ARM64EC'
p=folder/'Module.cpp';s=p.read_text()
anchor='NTSTATUS ProcessInit() {'
assert s.count(anchor)==1
s=s.replace(anchor,'#ifdef FEX_IOS_HOST\n#include "QueenNativeNav.h"\n#include "QueenNativeRhi.h"\n#endif\n\n'+anchor)
end='    std::this_thread::sleep_for(std::chrono::seconds(StartupSleep()));\n  }\n\n  return STATUS_SUCCESS;'
assert s.count(end)==1
s=s.replace(end,end.replace('  return STATUS_SUCCESS;','#ifdef FEX_IOS_HOST\n  InstallQueenNativeNav(MainModule);\n  InstallQueenNativeRhi(MainModule);\n#endif\n\n  return STATUS_SUCCESS;'))
for name in ['QueenNativeNav.h','QueenNativeNavKernel.h','QueenNativeNavFingerprint.h','QueenNativeRhi.h','QueenBoundShaderState.h','QueenBoundShaderRuntime.h','QueenBoundShaderFingerprint.h','QueenSelfExport.h']:
    dest=folder/name
    assert not dest.exists(),dest
    dest.write_bytes((here/name).read_bytes())
p.write_text(s)
p=folder/'libarm64ecfex.def';s=p.read_text()
assert 'QueenNativeLedgeFilter' not in s
p.write_text(s+'\n  QueenNativeLedgeFilter\n  QueenNativeBoundShaderState\n')
print('Queen native ledge-filter startup hook installed; no Module.S/game-file changes')

