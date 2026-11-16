#!/usr/bin/env python3
import hashlib,importlib.util,json,plistlib,shutil,sys
from pathlib import Path
root=Path.cwd();cfg=Path(sys.argv[1]).resolve();app=root/'build-out/reused/Payload/Madeira.app'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
newdll=root/'build-out/queen-nav/xtajit64-queen-nav.dll'
receipt=json.loads((root/'build-out/queen-nav/receipt.json').read_text());assert receipt['baseline_timestamp_normalized_identical'] and receipt['stock_preserved']
assert sha(newdll)==receipt['candidate_sha256']
shutil.copyfile(root/'build-out/new-dll/kernelbase.dll',app/'arm64ec-windows/kernelbase.dll')
expected=json.loads((cfg/'baseline660-files.json').read_text())
exceptions={
 'PlugIns/MadeiraJITHelper.appex/MadeiraJITHelper','PlugIns/MadeiraJITHelper.appex/Info.plist',
 'PlugIns/MadeiraMemoryHost.appex/MadeiraMemoryHost','PlugIns/MadeiraMemoryHost.appex/Info.plist',
 'Frameworks/StikJIT.framework/StikJIT','Frameworks/StikJIT.framework/Info.plist'}
verified=[]
for key,h in expected.items():
    rel=key.removeprefix('Payload/Madeira.app/');assert rel!=key
    if rel in exceptions:continue
    f=app/rel;assert f.is_file() and sha(f)==h,('660 runtime/data mismatch',rel)
    verified.append(rel)
shutil.copyfile(newdll,app/'arm64ec-windows/xtajit64-queen-nav.dll')
renderer=root/'build-out/queen-render/d3d11-queen-render.dll'
rr=json.loads((root/'build-out/queen-render/receipt.json').read_text());assert sha(renderer)==rr['candidate_sha256'] and rr['exports_imports_verified']
shutil.copyfile(renderer,app/'arm64ec-windows/d3d11-queen-v2.dll')
gr=json.loads((root/'build-out/queen-gs-native/native-gs-receipt.json').read_text());assert gr['changed_members']==['dxbc_converter_gs.o']
assert sha(root/'app/Madeira/libdxmt_combined.a')==gr['archive_sha256']
p=app/'Info.plist';info=plistlib.loads(p.read_bytes());assert info['CFBundleVersion']=='666'
info['BCDQueenNativeNav']=True
info['BCDValidationStatus']='QUEEN_RENDER_ARCHITECTURE_CANDIDATE_USER_TEST'
p.write_bytes(plistlib.dumps(info,fmt=plistlib.FMT_BINARY,sort_keys=False))
(root/'build-out/queen-nav-package-receipt.json').write_text(json.dumps({'baseline660_runtime_files_verified':len(verified),'signature_metadata_exceptions':sorted(exceptions),'added_runtime':'arm64ec-windows/xtajit64-queen-nav.dll','candidate':receipt,'renderer':rr,'native_gs':gr,'native_graphics_stage_family':True,'old_batching_enabled':False,'added_renderer':'arm64ec-windows/d3d11-queen-v2.dll','guest_leaf_contracts':['TlsGetValue','GetCurrentThreadId'],'native_api_bodies_unchanged':True,'copy_size_sampler':'existing 1/64 sampled exit only; no copy replacement','device_tested':False},indent=2))
spec=importlib.util.spec_from_file_location('signer',root/'tools/ota-variants.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.fakesign(str(app))



