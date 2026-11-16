#!/usr/bin/env python3
"""One FEX PE component baseline build; then Module.S-only incremental build.
Never replaces stock files. Fail closed if retained baseline does not reproduce.
Run from reconstructed source root; argument is candidate files directory.
"""
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
root=Path.cwd(); cfg=Path(sys.argv[1]).resolve(); out=root/'build-out/queen-alias';out.mkdir(parents=True,exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
def run(args,**kw):return subprocess.check_output(args,text=True,**kw)
assert run(['git','-C','FEX','rev-parse','HEAD']).strip()=='049a1b162e55c7b7328f7a86b53e0fbda05ddd22'
ship=root/'app/Madeira/arm64ec-windows/xtajit64.dll';stock=ship.read_bytes()
avx=root/'app/Madeira/arm64ec-windows/xtajit64-avx.dll';avxsha=sha(avx.read_bytes())
s=(root/'tools/build-xtajit64.sh').read_text()
a=s.index('echo "=== unpatched rebuild, compared with the committed xtajit64.dll ==="')
b=s.index('# madeira-bcd: the patched module replaces upstream',a)
s=s[:a]+s[b:]
end=s.index('\ngit -C FEX checkout -- "$CPUF"',s.index('python3 "$R/tools/patch-fex-ios-repne-bit-ops.py"'))
s=s[:end]+'\necho "Retained-overlay PE component baseline built; stock untouched"\n'
assert s.count('\nbuild\n')==1
assert 'cp "$B/Bin/libarm64ecfex.dll" "$SHIP"' not in s
script=out/'baseline-component.sh';script.write_text(s)
subprocess.run(['bash',str(script)],check=True)
B=Path(os.environ.get('FEX_ARM64EC_BUILD',str(root/'FEX/build-arm64ec')))
dll=B/'Bin/libarm64ecfex.dll';baseline=dll.read_bytes();(out/'baseline-xtajit64.dll').write_bytes(baseline)
spec=importlib.util.spec_from_file_location('pe',root/'tools/patch-wine-ntdll-sync.py');pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
a=pe.Pe(str(ship));b=pe.Pe(str(dll))
assert a.exports()==b.exports(),'Baseline exports/RVAs differ; stop, do not waive'
# Compare all mapped sections, excluding debug-only data. This is deliberately
# stricter than upstream warning-only fingerprinting: no drift gets shipped.
def sections(img):
    return {name:(va,vs,sha(img.d[raw:raw+min(vs,rs)])) for name,va,vs,raw,rs,ch in img.secs if not name.startswith('.debug') and name!='.buildid'}
assert sections(a)==sections(b),'Baseline mapped-section bytes/layout differ from donor; stop, no candidate'
assert sha(ship.read_bytes())==sha(stock) and sha(avx.read_bytes())==avxsha
objects=lambda:{str(p.relative_to(B)):sha(p.read_bytes()) for p in B.rglob('*') if p.is_file() and p.suffix in ('.o','.obj')}
before=objects()
source_before=(root/'FEX/Source/Windows/ARM64EC/Module.S').read_bytes()
subprocess.run([sys.executable,str(cfg/'apply-queen-alias.py'),str(root/'FEX')],check=True)
subprocess.run(['cmake','--build',str(B),'--target','arm64ecfex','-j2'],check=True)
after=objects();changed=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)]
assert len(changed)==1 and ('Module.S' in changed[0]),('Unexpected object changes',changed)
candidate=out/'xtajit64-queen-alias.dll';candidate.write_bytes(dll.read_bytes())
c=pe.Pe(str(candidate))
assert set(c.exports())==set(a.exports()),'Export set changed'
assert sha(ship.read_bytes())==sha(stock) and sha(avx.read_bytes())==avxsha
receipt={'baseline_sha256':sha(baseline),'donor_sha256':sha(stock),'baseline_mapped_sections_identical':True,'candidate_sha256':sha(candidate.read_bytes()),'changed_objects':changed,'source_before_sha256':sha(source_before),'source_after_sha256':sha((root/'FEX/Source/Windows/ARM64EC/Module.S').read_bytes()),'stock_preserved':True,'device_tested':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))

