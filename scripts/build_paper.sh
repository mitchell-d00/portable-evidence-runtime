#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
for DOC in core-papers/Portable_Evidence_Runtime core-papers/Validation_and_Publication_Review; do
  pandoc "$DOC.md" -f markdown+tex_math_dollars -t plain -o "$DOC.txt" --wrap=auto
  python3 -c 'from pathlib import Path; import sys; p=Path(sys.argv[1]); p.write_text("\n".join(line.rstrip() for line in p.read_text(encoding="utf-8").splitlines())+"\n", encoding="utf-8")' "$DOC.txt"
  pandoc "$DOC.md" -f markdown+tex_math_dollars -o "$DOC.pdf" --pdf-engine=xelatex -V mainfont='DejaVu Serif' -V sansfont='DejaVu Sans' -V geometry:margin=0.85in -V fontsize=10pt -V linestretch=1.18 -V colorlinks=true -V linkcolor=MidnightBlue -V urlcolor=MidnightBlue
done
# Keep the original archive paths usable; core-papers contains the editable source.
for EXT in md txt pdf; do
  cp "core-papers/Portable_Evidence_Runtime.$EXT" "paper/Portable_Evidence_Runtime.$EXT"
done
