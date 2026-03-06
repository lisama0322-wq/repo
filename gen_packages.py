#!/usr/bin/env python3
"""Generate Packages, Packages.gz, Packages.bz2 for a jailbreak repo."""
import os, hashlib, gzip, bz2, tarfile, io, lzma, glob

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DEBS_DIR = os.path.join(REPO_DIR, "debs")

def extract_control(deb_path):
    """Extract control file content from a .deb file."""
    with open(deb_path, 'rb') as f:
        sig = f.read(8)  # ar signature "!<arch>\n"
        while True:
            header = f.read(60)
            if len(header) < 60:
                break
            name = header[0:16].decode('ascii', errors='ignore').strip()
            fsize = int(header[48:58].decode().strip())
            if 'control' in name:
                cdata = f.read(fsize)
                # Try different compression formats
                tf = None
                for mode in ['r:gz', 'r:xz', 'r:']:
                    try:
                        tf = tarfile.open(fileobj=io.BytesIO(cdata), mode=mode)
                        break
                    except:
                        pass
                if tf is None:
                    try:
                        dec = lzma.decompress(cdata)
                        tf = tarfile.open(fileobj=io.BytesIO(dec), mode='r:')
                    except:
                        return None
                for m in tf.getmembers():
                    if m.name.endswith('control') and not m.isdir():
                        return tf.extractfile(m).read().decode('utf-8', errors='replace').strip()
                return None
            else:
                f.seek(fsize + (fsize % 2), 1)
    return None

def get_hashes(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    return {
        'size': len(data),
        'md5': hashlib.md5(data).hexdigest(),
        'sha256': hashlib.sha256(data).hexdigest(),
    }

def main():
    entries = []
    for deb in sorted(glob.glob(os.path.join(DEBS_DIR, "*.deb"))):
        control = extract_control(deb)
        if not control:
            print(f"WARNING: Could not extract control from {deb}")
            continue
        hashes = get_hashes(deb)
        filename = "debs/" + os.path.basename(deb)
        entry = control + "\n"
        entry += f"Filename: {filename}\n"
        entry += f"Size: {hashes['size']}\n"
        entry += f"MD5sum: {hashes['md5']}\n"
        entry += f"SHA256: {hashes['sha256']}\n"
        entries.append(entry)
        print(f"Added: {os.path.basename(deb)}")

    packages = "\n".join(entries) + "\n"

    # Write Packages
    pkg_path = os.path.join(REPO_DIR, "Packages")
    with open(pkg_path, 'w', encoding='utf-8') as f:
        f.write(packages)
    print(f"Written: Packages ({len(packages)} bytes)")

    # Write Packages.gz
    pkg_gz = os.path.join(REPO_DIR, "Packages.gz")
    with gzip.open(pkg_gz, 'wb') as f:
        f.write(packages.encode('utf-8'))
    print(f"Written: Packages.gz")

    # Write Packages.bz2
    pkg_bz2 = os.path.join(REPO_DIR, "Packages.bz2")
    with bz2.open(pkg_bz2, 'wb') as f:
        f.write(packages.encode('utf-8'))
    print(f"Written: Packages.bz2")

    print("Done!")

if __name__ == '__main__':
    main()
