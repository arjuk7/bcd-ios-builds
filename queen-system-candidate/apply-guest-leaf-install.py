#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).resolve().parent
p=root/'Source/Windows/ARM64EC/Module.cpp';s=p.read_text()
a='#include "QueenNativeRhi.h"';assert s.count(a)==1
s=s.replace(a,a+'\n#include "QueenGuestLeafInstall.h"')
a='  InstallQueenNativeRhi(MainModule);';assert s.count(a)==1
s=s.replace(a,a+'\n  InstallQueenGuestLeaf(MainModule);')
for n in ['QueenGuestLeafInstall.h','QueenGuestLeafBytes.h','QueenGuestLeafFingerprint.h']:
 dest=p.parent/n;assert not dest.exists();dest.write_bytes((here/n).read_bytes())
p.write_text(s)
print('Queen guest leaf installer: full TLS/thread identity contracts, originals retained')
