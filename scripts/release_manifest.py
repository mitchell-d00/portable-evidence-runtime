"""Write/check the complete Git-visible release inventory (not a signature)."""
import argparse
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    names = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT
    ).decode().split('\0')
    entries = []
    for name in sorted(set(names) - {'', 'SHA256SUMS'}):
        path = ROOT / name
        if not path.is_file():
            raise SystemExit('Missing release file: ' + name)
        entries.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + name)
    expected = '\n'.join(entries) + '\n'
    target = ROOT / 'SHA256SUMS'
    if args.write:
        target.write_text(expected, encoding='utf-8')
        print(f'Wrote {len(entries)} release digests')
    elif not target.exists() or target.read_text(encoding='utf-8') != expected:
        raise SystemExit('Release inventory changed; regenerate SHA256SUMS after final builds and tests')
    else:
        print(f'PASS: {len(entries)} release digests and complete inventory')


if __name__ == '__main__':
    main()
