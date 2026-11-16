#!/bin/bash
set -euo pipefail
ORCH="$GITHUB_WORKSPACE/queen-system-candidate"
cd "$GITHUB_WORKSPACE"
mkdir inputs
# Existing private retained release only; no cross-account token or signed URL.
test "$(gh api "repos/$GITHUB_REPOSITORY" --jq '.private == true and .owner.login == "arjuk7"')" = true
gh release download bcd-retained-v653-native654-v1 --repo "$GITHUB_REPOSITORY" --dir inputs --pattern '*.bundle' --pattern donor.zip --pattern retained-native-inputs.zip --pattern '*metadata.json' --pattern transport-manifest.json
python3 - <<'PY'
import hashlib,json
from pathlib import Path
p=Path('inputs');sha=lambda f:hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
fs=[f for f in p.glob('*.bundle') if f.stat().st_size==238842649 and sha(f)=='1994d99c930f0aa38c1c1d66731560979f1ab309ebe8ad096a343fbd4387b09f'];assert len(fs)==1
if fs[0].name!='source.bundle':fs[0].rename(p/'source.bundle')
assert sha(p/'transport-manifest.json')=='31e3e289d437caa5ff577d168575b3018427910daebc06b2d284c8d20f9c4ee2'
for n,v in json.loads((p/'transport-manifest.json').read_text())['files'].items():
 assert '/' not in n and '\\' not in n
 assert (p/n).stat().st_size==v['bytes'] and sha(p/n)==v['sha256'],n
PY
git init source
ref=$(git bundle list-heads inputs/source.bundle | awk 'NR==1{print $2}')
git -C source fetch "$GITHUB_WORKSPACE/inputs/source.bundle" "$ref"
git -C source checkout --detach dbbb5bf538f30b46ebbcf18262e5a2e10710be97
python3 - <<'PY'
import base64,gzip,hashlib
from pathlib import Path
b=gzip.decompress(base64.b64decode(Path('queen-system-candidate/touch-update.patch.gz.b64').read_text()))
assert hashlib.sha256(b).hexdigest()=='e9b6287ec4d5fb904245bea473dfc49b2ea4cd5e2cda2e834554d4a30bad00a3'
Path('inputs/touch.patch').write_bytes(b)
PY
git -C source apply --index --binary "$GITHUB_WORKSPACE/inputs/touch.patch"
test "$(git -C source write-tree)" = 13d3e63472decd675bfab63c9237aa95114f6d98
git -C source submodule update --init --recursive --depth 1 --jobs 4 FEX dxmt
cd source
# Migration was explicitly authorized; retain donor origin, add only new private app provenance.
python3 - <<'PY'
from pathlib import Path
p=Path('tools/touch-packs/reuse-v653-donor.py');s=p.read_text()
a="'arjuks-9/bcd-touch', 'arjuk8-dot/bcd-ios-builds'"
assert s.count(a)==1
p.write_text(s.replace(a,a+", 'arjuk7/bcd-ios-builds'"))
PY
mkdir -p build-out toolchains
# Exact previous compiler; do not silently substitute Xcode27.
test -d /Applications/Xcode_26.3.app
sudo xcode-select -s /Applications/Xcode_26.3.app/Contents/Developer
python3 tools/touch-packs/reuse-v653-donor.py prepare --artifact ../inputs/donor.zip --output build-out/donor
python3 tools/touch-packs/reuse-v653-donor.py stage --prepared build-out/donor --repo "$PWD"
python3 tools/ci/restore-native-link-inputs.py --artifact ../inputs/retained-native-inputs.zip --artifact-metadata ../inputs/retained-artifact-metadata.json --run-metadata ../inputs/retained-run-metadata.json --job-metadata ../inputs/retained-job-metadata.json --repo "$PWD" --receipt build-out/native-link-inputs.json
curl -fL --retry 2 https://github.com/mstorsjo/llvm-mingw/releases/download/20260421/llvm-mingw-20260421-ucrt-macos-universal.tar.xz -o ../inputs/mingw.tar.xz
echo 'bd85a3975723815cef28dbbd2ca2cb0c926f6b348a12a0453f39f7af273cb3f7  ../inputs/mingw.tar.xz' | shasum -a256 -c -
tar -xJf ../inputs/mingw.tar.xz -C toolchains
export MINGW="$PWD/toolchains/llvm-mingw-20260421-ucrt-macos-universal/bin"
command -v cmake >/dev/null; command -v ninja >/dev/null
python3 "$ORCH/build-target.py" "$ORCH"
export QUEEN_RENDER_PATCH="$ORCH/queen-implicit-submission-batching.patch"
bash "$ORCH/render-build/build-queen-render.sh"
# Preserve prior659 DXMT object, not just old654 retained archive.
python3 "$ORCH/queen-native-candidate/compile-one-object.py" --repo "$PWD" --output "$PWD/build-out/queen-native"
mkdir -p build-out/new-dll
"$MINGW/clang" --target=aarch64-w64-windows-gnu -c "$ORCH/queen-tls-candidate/tls-single-teb.S" -o build-out/tls-leaf.o
python3 "$ORCH/queen-tls-candidate/patch-shipped.py" app/Madeira/arm64ec-windows/kernelbase.dll build-out/tls-leaf.o build-out/new-dll/kernelbase.dll
python3 "$ORCH/queen-tls-candidate/check-native.py" "$MINGW/llvm-objdump" build-out/new-dll/kernelbase.dll
git apply --check "$ORCH/queen-nav-app-and-badge.patch"
git apply "$ORCH/queen-nav-app-and-badge.patch"
python3 "$ORCH/apply-queen-render-app.py" "$PWD"
git apply --check "$ORCH/inscryption-lower-left.patch"
git apply "$ORCH/inscryption-lower-left.patch"
python3 tools/stikjit-interface-compat.py app/Frameworks/StikJIT.xcframework
python3 - <<'PY'
import datetime,os,plistlib
from pathlib import Path
p=Path('app/Madeira/Info.plist');d=plistlib.loads(p.read_bytes());d.update(CFBundleVersion='664',CFBundleShortVersionString='0.1.664',MadeiraCommit=os.environ['GITHUB_SHA'],MadeiraRepo=os.environ['GITHUB_REPOSITORY'],MadeiraBuilt=datetime.datetime.now(datetime.timezone.utc).isoformat(),BCDDeviceValidationStatus='NOT_RUN',BCDFullValidationRunStatus='NOT_RUN');p.write_bytes(plistlib.dumps(d,fmt=plistlib.FMT_XML,sort_keys=False))
PY
xcodebuild -project app/Madeira.xcodeproj -scheme Madeira -sdk iphoneos -configuration Debug CODE_SIGNING_ALLOWED=NO archive -archivePath build-out/Madeira.xcarchive > build-out/archive.log 2>&1 || { tail -150 build-out/archive.log; exit 1; }
python3 tools/touch-packs/reuse-v653-donor.py assemble --prepared build-out/donor --compiled-app build-out/Madeira.xcarchive/Products/Applications/Madeira.app --source "$GITHUB_SHA" --app-repository "$GITHUB_REPOSITORY" --output build-out/reused
python3 tools/touch-packs/reuse-v653-donor.py verify --output build-out/reused
python3 "$ORCH/package-candidate.py" "$ORCH"
codesign --verify --deep --strict build-out/reused/Payload/Madeira.app
(cd build-out/reused && zip -qry ../BCD-664-Queen-System-unsigned.ipa Payload)
source_sha=$(shasum -a256 build-out/BCD-664-Queen-System-unsigned.ipa | awk '{print $1}')
# Preserve the installed com.thebcd69.bcd slot; raw donor is com.arjunkl.bcdtouch.
python3 tools/touch-packs/package-sideload.py build-out/BCD-664-Queen-System-unsigned.ipa --mode existing --output build-out/existing-update --expected-source "$GITHUB_SHA" --expected-ipa-sha "$source_sha"
cp build-out/existing-update/BCD-Touch-update-existing-unsigned.ipa build-out/BCD-664-Queen-System-update.ipa
shasum -a256 build-out/BCD-664-Queen-System-update.ipa > build-out/ipa.sha256



