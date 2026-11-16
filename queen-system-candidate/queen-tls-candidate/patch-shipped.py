"""Patch only the verified leaf body in the exact659prebuilt DLL.
Preserve every byte outside76bytecode span including adjacentECmetadata.
"""
import hashlib,struct,sys,json
from pathlib import Path
old,body,out=map(Path,sys.argv[1:]);d=old.read_bytes();obj=body.read_bytes()
# Read native COFF .text directly; llvm-objcopy's COFF output mode is not a raw leaf.
machine,nsects,_,_,_,optional,_=struct.unpack_from('<HHIIIHH',obj,0)
assert machine==0xaa64,'Expected compiled AArch64 COFF object'
sections=[]
for i in range(nsects):
 q=20+optional+40*i
 if obj[q:q+8].rstrip(b'\0')==b'.text':
  rawsize,raw=struct.unpack_from('<II',obj,q+16)
  relocations=struct.unpack_from('<H',obj,q+32)[0]
  assert relocations==0,'Leaf must be relocation-free'
  sections.append(obj[raw:raw+rawsize])
assert len(sections)==1
b=sections[0]
if len(b)>76:
 assert not any(b[76:]),'Unexpected extra instructions after leaf'
 b=b[:76]
assert hashlib.sha256(d).hexdigest()=='5fde0bcb58a51a93fed0c564ebb32596d52528ccc4afd255e98f62f10fbb954c'
assert len(b)==76,'Leaf body must fit exact76byte span'
oldbody=bytes.fromhex('1ffc00715f6a00b988000054484e208b00414af9c0035fd6080001511f011071a3000054e0031faae80a8052486a00b9c0035fd649c24bf9690000b4205968f8c0035fd6e0031faac0035fd6')
a=0x6d470;assert d[a:a+76]==oldbody
# Fixed leaf ABI: MOVx8,x18, no stack/calls; exact assembled bytes independent of assembler labels.
expected=[0xaa1203e8,0xb900691f,0x7101001f,0x54000082,0x8b204d09,0xf94a4120,0xd65f03c0,0x51010000,0x7110001f,0x540000a2,0xf94bc109,0xb40000a9,0xf8605920,0xd65f03c0,0x52800ae9,0xb9006909,0xaa1f03e0,0xd65f03c0,0xd503201f]
assert b==struct.pack('<19I',*expected),'Compiled leaf differs from reviewed instructions'
r=d[:a]+b+d[a+76:];assert r[:a]==d[:a] and r[a+76:]==d[a+76:]
out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(r)
Path('build-out/tls-byte-replacement.json').write_text(json.dumps({'offset':a,'length':76,'old_sha256':hashlib.sha256(d).hexdigest(),'new_sha256':hashlib.sha256(r).hexdigest(),'outside_span':'byte-identical','adjacent_word_preserved':d[a+76:a+80].hex()},indent=2))
print('PASS exact76byte leaf replacement; every other byte unchanged')

