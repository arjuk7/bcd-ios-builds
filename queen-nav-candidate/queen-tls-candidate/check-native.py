import re,subprocess,sys
from pathlib import Path
objdump,dll=sys.argv[1:]
s=subprocess.check_output([objdump,'-d','--triple=aarch64-w64-windows-gnu','--disassemble-symbols=TlsGetValue',dll],text=True)
Path('build-out/tls-native-disassembly.txt').write_text(s)
m=re.search(r'<#?TlsGetValue>:',s);assert m,s[-2000:]
body=s[m.end():].split('\n\n',1)[0]
x18=[l for l in body.splitlines() if re.search(r'\bx18\b',l)]
assert len(x18)==1,x18
assert re.search(r'\bmov\s+x(?:[0-9]|1[0-7]|19|2[0-8]),\s*x18\b',x18[0]),x18
assert not re.search(r'\bbl(?:r)?\s',body),body
assert re.search(r'\bret\b',body),body
print('PASS actual ARM64EC TLS body: one ordinary-register TEB capture, no other x18 use or calls')

