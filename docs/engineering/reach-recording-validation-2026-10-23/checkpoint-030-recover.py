"""Verify every identified ZIP byte before extracting to a fresh directory."""
import argparse,hashlib,io,json,pathlib,stat,zipfile

def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=pathlib.Path,required=True);p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
    c=json.loads(a.checkpoint.read_text());m=json.loads(a.manifest.read_text());archive=c['archive'];base=a.checkpoint.parent
    def sha(raw):return hashlib.sha256(raw).hexdigest()
    parts=[]
    for item in archive['parts']:
        name=pathlib.PurePosixPath(item['path']);assert not name.is_absolute() and '..' not in name.parts
        raw=(base/name).read_bytes();assert len(raw)==item['bytes'] and sha(raw)==item['sha256'];parts.append(raw)
    raw=b''.join(parts);assert len(raw)==archive['bytes'] and sha(raw)==archive['sha256']
    members={x['path']:x for x in m['members']};assert len(members)==len(m['members'])==archive['member_count']
    assert not a.output.exists();assert not a.receipt.exists()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist();assert len(names)==len(set(names)) and set(names)==set(members)
        assert z.testzip() is None
        for info in z.infolist():
            name=pathlib.PurePosixPath(info.filename);assert not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename and str(name)==info.filename
            assert not info.is_dir() and not stat.S_ISLNK(info.external_attr>>16)
            data=z.read(info.filename);item=members[info.filename];assert len(data)==item['bytes'] and sha(data)==item['sha256']
        a.output.mkdir(parents=True)
        for name in names:
            dest=a.output/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    receipt={'checkpoint':c['checkpoint'],'archive_sha256':sha(raw),'archive_bytes':len(raw),'members':len(members),'zip_crc':'passed','exact_membership':'passed','member_hashes':'passed','safe_paths':'passed','output':str(a.output.resolve()),'historical_product_rerun':False}
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
