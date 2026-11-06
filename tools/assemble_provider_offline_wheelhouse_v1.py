#!/usr/bin/env python3
"""Assemble a review-only, offline wheelhouse and separate hash-lock overlays."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, tempfile, urllib.error, urllib.parse, urllib.request, zipfile
from email.parser import Parser
from pathlib import Path

SOURCE = {"cffi":"2.1.1","pycparser":"3.12","colorama":"0.4.6","pygments":"2.21.0"}
PYPI = {
 "cryptography":("50.0.2","https://github.com/pyca/cryptography"),
 "iniconfig":("2.3.1","https://github.com/pytest-dev/iniconfig"),
 "packaging":("26.3","https://github.com/pypa/packaging"),
 "pluggy":("1.7.0","https://github.com/pytest-dev/pluggy"),
 "pytest":("8.4.2","https://github.com/pytest-dev/pytest"),
}
ALL = {**SOURCE, **{k:v[0] for k,v in PYPI.items()}}
HEADER = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)")

def canon(s): return re.sub(r"[-_.]+","-",s).lower()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def metadata(path):
 with zipfile.ZipFile(path) as z:
  names=[n for n in z.namelist() if n.endswith(".dist-info/METADATA") and n.count("/")==1]
  if len(names)!=1: raise RuntimeError("WHEEL_METADATA_CARDINALITY_INVALID:"+Path(path).name)
  m=Parser().parsestr(z.read(names[0]).decode("utf-8"))
 if not m.get("Name") or not m.get("Version"): raise RuntimeError("WHEEL_METADATA_MISSING")
 return canon(m["Name"]),m["Version"]
def wheel_map(root):
 files=sorted(Path(root).glob("*.whl"))
 if len(files)!=9: raise RuntimeError(f"WHEELHOUSE_FILE_COUNT_MISMATCH:{len(files)}")
 out={}
 for p in files:
  n,v=metadata(p)
  if n in out or ALL.get(n)!=v: raise RuntimeError(f"WHEELHOUSE_PACKAGE_OR_VERSION_INVALID:{n}:{v}")
  out[n]=p
 if set(out)!=set(ALL): raise RuntimeError("WHEELHOUSE_PACKAGE_SET_MISMATCH")
 return out
def cli_for(py):
 code="import json; from importlib.metadata import entry_points; print(json.dumps([e.name for e in entry_points(group='console_scripts') if e.name in ('pypi-attestation', 'pypi-attestations')]))"
 names=json.loads(subprocess.run([str(py),"-c",code],capture_output=True,text=True,check=True).stdout)
 if len(names)!=1: raise RuntimeError("PYPI_ATTESTATION_CLI_AMBIGUOUS")
 path=Path(py).resolve().parent/(names[0]+".exe")
 if not path.is_file(): raise RuntimeError("PYPI_ATTESTATION_CLI_MISSING")
 return path
def verify_pypi(name, version, repo, wheel, cli, temp):
 url="https://pypi.org/integrity/"+urllib.parse.quote(name,safe="")+"/"+urllib.parse.quote(version,safe="")+"/"+urllib.parse.quote(wheel.name,safe="")+"/provenance"
 row={"package":name,"version":version,"filename":wheel.name,"sha256":sha(wheel),"expected_publisher_repository":repo,"provenance_url":url,"http_status":None,"verification_status":"BLOCKED_NOT_VERIFIED","verifier_exit_code":None,"verifier_detail":""}
 try:
  req=urllib.request.Request(url,headers={"Accept":"application/vnd.pypi.integrity.v1+json"})
  with urllib.request.urlopen(req,timeout=30) as resp: row["http_status"]=resp.status; raw=resp.read()
  prov=Path(temp)/(wheel.name+".provenance.json"); prov.write_bytes(raw)
  result=subprocess.run([str(cli),"verify","pypi","--repository",repo,"--provenance-file",str(prov),str(wheel)],capture_output=True,text=True)
  row["verifier_exit_code"]=result.returncode; row["verifier_detail"]=(result.stdout+"\n"+result.stderr).strip()[:1200]
  row["verification_status"]="PASS_CRYPTOGRAPHICALLY_VERIFIED_EXPECTED_REPOSITORY" if result.returncode==0 else "BLOCKED_ATTESTATION_OR_REPOSITORY_IDENTITY"
 except urllib.error.HTTPError as e:
  row["http_status"]=e.code; row["verification_status"]="BLOCKED_PROVENANCE_MISSING" if e.code==404 else "BLOCKED_PROVENANCE_LOOKUP_ERROR"; row["verifier_detail"]=f"HTTP {e.code}"
 except (OSError, urllib.error.URLError, subprocess.SubprocessError) as e:
  row["verification_status"]="BLOCKED_PROVENANCE_LOOKUP_OR_VERIFIER_ERROR"; row["verifier_detail"]=(type(e).__name__+":"+str(e))[:1200]
 return row
def add_hash(text, package, version, digest):
 if not re.fullmatch(r"[0-9a-f]{64}",digest): raise ValueError("CUSTOM_WHEEL_SHA256_INVALID")
 lines=text.splitlines(); heads=[]
 for i,line in enumerate(lines):
  m=HEADER.match(line)
  if m: heads.append((i,canon(m.group(1)),m.group(2)))
 matches=[x for x in heads if x[1]==canon(package)]
 if len(matches)!=1: raise RuntimeError("LOCK_PACKAGE_CARDINALITY_INVALID:"+package)
 start,_,got=matches[0]
 if got!=version: raise RuntimeError("LOCK_PACKAGE_VERSION_MISMATCH:"+package+":"+got)
 end=next((i for i,_,_ in heads if i>start),len(lines)); section=lines[start:end]
 if any("--hash=sha256:"+digest in line for line in section): return text
 offsets=[start+o for o,line in enumerate(section) if "--hash=sha256:" in line]
 if not offsets: raise RuntimeError("LOCK_PACKAGE_HAS_NO_HASHES:"+package)
 last=offsets[-1]
 if not lines[last].rstrip().endswith("\\"): lines[last]=lines[last].rstrip()+" \\"
 lines.insert(last+1,"    --hash=sha256:"+digest)
 return "\n".join(lines)+"\n"
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--output-root",required=True,type=Path); p.add_argument("--verifier-python",required=True,type=Path)
 a=p.parse_args(); root=a.output_root.resolve(); wheel_dir=root/"wheels"; house=root/"wheelhouse"; locks=root/"locks"
 mf=root/"source-build-manifest.json"; report_path=root/"pypi-provenance-report.json"; overlay=root/"overlay-locks"
 if not (wheel_dir.is_dir() and house.is_dir() and locks.is_dir() and mf.is_file()): raise RuntimeError("SOURCE_WHEELHOUSE_LOCKS_OR_MANIFEST_MISSING")
 if overlay.exists(): raise RuntimeError("OVERLAY_LOCK_DIRECTORY_ALREADY_EXISTS")
 manifest=json.loads(mf.read_text(encoding="utf-8"))
 if manifest.get("production_approved") is not False or manifest.get("bootstrap_approved") is not False: raise RuntimeError("SOURCE_MANIFEST_BOUNDARY_INVALID")
 wm=wheel_map(house); cli=cli_for(a.verifier_python.resolve()); checks=[]
 with tempfile.TemporaryDirectory(prefix="forexai-pypi-attestation-") as t:
  for name,(version,repo) in PYPI.items(): checks.append(verify_pypi(name,version,repo,wm[name],cli,t))
 passed=all(x["verification_status"]=="PASS_CRYPTOGRAPHICALLY_VERIFIED_EXPECTED_REPOSITORY" for x in checks)
 report={"schema":"forexai.provider_source_wheelhouse_pypi_provenance.v1","status":"PASS_CRYPTOGRAPHIC_VERIFICATION" if passed else "BLOCKED_PYPI_PROVENANCE_VERIFICATION","wheel_count":len(wm),"pypi_verified_wheel_count":len(checks),"verifier":"pypi-attestations==0.0.30","wheels":checks}
 report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 if not passed: raise RuntimeError("PYPI_SOURCE_WHEELHOUSE_PROVENANCE_GATE_FAILED")
 source_records={x["package"]:x for x in manifest.get("wheels",[])}
 if set(source_records)!=set(SOURCE): raise RuntimeError("SOURCE_WHEEL_MANIFEST_PACKAGE_SET_INVALID")
 custom={}
 for name,version in SOURCE.items():
  entry=source_records[name]; path=wheel_dir/entry["filename"]
  if entry.get("version")!=version or not path.is_file() or metadata(path)!=(name,version) or sha(path)!=entry["sha256"]: raise RuntimeError("SOURCE_WHEEL_MANIFEST_HASH_OR_METADATA_INVALID:"+name)
  wm[name].unlink(); dst=house/path.name; shutil.copy2(path,dst)
  if sha(dst)!=entry["sha256"]: raise RuntimeError("SOURCE_WHEELHOUSE_COPY_HASH_MISMATCH:"+name)
  custom[name]=entry["sha256"]
 wm=wheel_map(house)
 rt=locks/"requirements-provider.lock.txt"; test=locks/"requirements-provider-test.lock.txt"
 if not rt.is_file() or not test.is_file(): raise RuntimeError("CANDIDATE_LOCKS_MISSING")
 rtext=rt.read_text(encoding="utf-8"); ttext=test.read_text(encoding="utf-8")
 for name in ("cffi","pycparser"): rtext=add_hash(rtext,name,SOURCE[name],custom[name])
 for name in SOURCE: ttext=add_hash(ttext,name,SOURCE[name],custom[name])
 overlay.mkdir()
 ro=overlay/rt.name; to=overlay/test.name
 ro.write_text(rtext,encoding="utf-8"); to.write_text(ttext,encoding="utf-8")
 for name,digest in custom.items():
  if name in ("cffi","pycparser") and f"--hash=sha256:{digest}" not in rtext: raise RuntimeError(f"RUNTIME_OVERLAY_HASH_MISSING:{name}")
  if f"--hash=sha256:{digest}" not in ttext: raise RuntimeError(f"TEST_OVERLAY_HASH_MISSING:{name}")
 wr=[]
 for name,path in sorted(wm.items()):
  ver=metadata(path)[1]; wr.append({"package":name,"version":ver,"filename":path.name,"sha256":sha(path),"origin":"SOURCE_BUILT_CANDIDATE" if name in SOURCE else "PYPI_ATTESTATION_VERIFIED"})
 whmanifest={"schema":"forexai.provider_offline_wheelhouse_candidate.v1","status":"WHEELHOUSE_CANDIDATE_NOT_APPROVED","production_approved":False,"bootstrap_approved":False,"source_build_manifest_sha256":sha(mf),"pypi_provenance_report_sha256":sha(report_path),"runtime_lock_sha256":sha(ro),"test_lock_sha256":sha(to),"base_runtime_lock_sha256":sha(rt),"base_test_lock_sha256":sha(test),"additional_custom_wheel_hashes":custom,"wheel_count":len(wr),"wheels":wr,"policy":"Offline-test candidate only. The pycparser, colorama, and Pygments source commits and release tags lack verified signatures. Their exact commit/tag targets and narrow metadata-only changed-file, blob, and patch allowlists are pinned, but independent source review remains required. Build and helper-tool dependency closures are hash-locked and offline-tested in review-only candidate artifacts; they are not approved for production Bootstrap. Not wired into production Bootstrap."}
 (root/"wheelhouse-manifest.json").write_text(json.dumps(whmanifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("PYPI_SOURCE_WHEEL_ATTESTATIONS=PASS"); print("SOURCE_BUILT_HASH_OVERLAY=PASS"); print("OFFLINE_WHEELHOUSE_PACKAGE_COUNT=9")
 print("OFFLINE_RUNTIME_LOCK_SHA256="+whmanifest["runtime_lock_sha256"]); print("OFFLINE_TEST_LOCK_SHA256="+whmanifest["test_lock_sha256"])
 print("PRODUCTION_APPROVED=false"); print("BOOTSTRAP_APPROVED=false")
if __name__=="__main__":
 try: main()
 except (OSError,RuntimeError,ValueError,zipfile.BadZipFile,json.JSONDecodeError,subprocess.CalledProcessError) as e:
  print(f"OFFLINE_WHEELHOUSE_ASSEMBLY_BLOCKED={type(e).__name__}:{e}"); raise SystemExit(1)
