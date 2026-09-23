"""Verify the label-only FCStd repair and reopen it without a save/recompute.

Run through tools/freecad/run_macos.py. SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import FreeCAD as A

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preserve_document_label import compare_archives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', default='Flan36')
    parser.add_argument('--report', type=Path, default=Path('validation/revI-document-label.json'))
    argv = sys.argv[1:]
    if os.environ.get('FILO_FREECAD_SUBPROCESS') == '1':
        target = str(Path(__file__).resolve())
        argv = argv[argv.index(target)+1:]
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    source, output = args.source.resolve(), args.output.resolve()
    before, after = source.read_bytes(), output.read_bytes()
    proof = compare_archives(before, after, args.label)
    doc = A.openDocument(str(output))
    try:
        if doc.Label != args.label:
            raise AssertionError(('unexpected native label', doc.Label))
        errors = [{'object': obj.Name, 'state': list(obj.State)} for obj in doc.Objects
                  if any('invalid' in str(s).lower() or 'error' in str(s).lower() for s in obj.State)]
        if errors:
            raise AssertionError(('native document errors on open', errors))
        native = {'opened': True, 'label': doc.Label, 'object_count': len(doc.Objects),
                  'document_errors': errors, 'explicit_recompute_requested': False,
                  'save_requested': False, 'geometry_revalidation_claimed': False,
                  'freecad_version': '.'.join(A.Version()[:3])}
    finally:
        A.closeDocument(doc.Name)
    if source.read_bytes() != before or output.read_bytes() != after:
        raise AssertionError('Opening changed an immutable FCStd file')
    paths = ['tools/freecad/preserve_document_label.py', 'tools/freecad/check_document_label.py']
    proof.update(passed=True, physical_acceptance=False, source_unchanged=True,
                 output_unchanged_on_open=True, native_open=native,
                 source=str(source.relative_to(root)), output=str(output.relative_to(root)),
                 scope='Root document label only. All other uncompressed and compressed ZIP member bytes, including geometry and GUI, are identical to the analyzed source; no new full geometry recompute validation.',
                 inputs=[{'path': p, 'sha256': hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],
                 reproduce=[
                     'python3 tools/freecad/preserve_document_label.py --source build/slim-source/Flan36.FCStd --output build/label-preserved/Flan36.FCStd --label Flan36',
                     'python3 tools/freecad/run_macos.py tools/freecad/check_document_label.py --source build/slim-source/Flan36.FCStd --output build/label-preserved/Flan36.FCStd --label Flan36 --report validation/revI-document-label.json'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(proof, indent=2)+'\n')
    sys.__stdout__.write(json.dumps({'passed': True, 'source_sha256': proof['source_sha256'],
                                   'output_sha256': proof['output_sha256'], 'native_open': native})+'\n')
    sys.__stdout__.flush()


if __name__ == '__main__':
    main()
