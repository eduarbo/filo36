"""Restore only an FCStd document label, preserving every other ZIP member.

This operates on a closed file, without loading, recomputing or saving a CAD
document. The output must be a new path. Standard single-disk, non-ZIP64 FCStd
archives with a stored or deflated Document.xml are supported; unsupported
containers fail closed. Compressed bytes and member attributes are retained for
every other member. Installer callers may atomically replace their temporary
file with the verified output after this function returns.

SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
from xml.parsers import expat
from xml.sax.saxutils import escape
import zipfile
import zlib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def label_span(data):
    """Locate the root document's Label value without serializing its XML."""
    parser = expat.ParserCreate()
    stack, found = [], []

    def start(name, attrs):
        stack.append((name, attrs))
        if ([item[0] for item in stack] == ['Document', 'Properties', 'Property', 'String']
                and stack[-2][1].get('name') == 'Label'):
            offset = parser.CurrentByteIndex
            tag = re.match(rb'''<String\b(?:[^>"']|"[^"]*"|'[^']*')*>''', data[offset:])
            if not tag:
                raise ValueError('Cannot locate Label String tag')
            value = re.search(rb'''\bvalue\s*=\s*(["'])(.*?)\1''', tag.group(), re.S)
            if not value or 'value' not in attrs:
                raise ValueError('Cannot locate Label value attribute')
            found.append((offset + value.start(2), offset + value.end(2),
                          attrs['value'], value.group(1)))

    parser.StartElementHandler = start
    parser.EndElementHandler = lambda name: stack.pop()
    parser.Parse(data, True)
    if len(found) != 1:
        raise ValueError('Expected exactly one root Document Label')
    return found[0]


def replace_label_xml(data, label):
    start, end, old, quote = label_span(data)
    escaped = escape(label, {'"': '&quot;', "'": '&apos;'})
    changed = data[:start] + escaped.encode('utf-8') + data[end:]
    if label_span(changed)[2] != label:
        raise ValueError('Changed XML does not contain the requested label')
    return changed, {'input_label': old, 'output_label': label,
                     'value_start_byte': start, 'old_value_bytes': end-start,
                     'new_value_bytes': len(escaped.encode('utf-8'))}


def _rewrite_document_member(raw, changed_xml):
    """Copy existing ZIP entries verbatim and update only Document.xml data."""
    with zipfile.ZipFile(io.BytesIO(raw)) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP members are unsupported')
        member = source.getinfo('Document.xml')
        central_start = source.start_dir
        infos = source.infolist()
    end = raw.rfind(b'PK\x05\x06')
    if end < 0:
        raise ValueError('Missing ZIP end record')
    fields = struct.unpack_from('<4s4H2LH', raw, end)
    _, disk, directory_disk, disk_count, count, directory_size, directory_start, comment_size = fields
    if (disk or directory_disk or disk_count != count or count != len(infos)
            or count >= 65535 or directory_start != central_start
            or directory_start + directory_size != end
            or end + 22 + comment_size != len(raw)
            or len(raw) >= 0xffffffff):
        raise ValueError('Only ordinary single-disk, non-ZIP64 archives are supported')
    if member.flag_bits & 9 or member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise ValueError('Encrypted, descriptor-based or unsupported Document.xml compression')
    local = member.header_offset
    if raw[local:local+4] != b'PK\x03\x04':
        raise ValueError('Missing Document.xml local header')
    name_len, extra_len = struct.unpack_from('<2H', raw, local+26)
    data_start = local + 30 + name_len + extra_len
    data_end = data_start + member.compress_size
    if struct.unpack_from('<3L', raw, local+14) != (member.CRC, member.compress_size, member.file_size):
        raise ValueError('Document.xml local sizes differ from the central directory')
    if member.compress_type == zipfile.ZIP_DEFLATED:
        compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
        compressed = compressor.compress(changed_xml) + compressor.flush()
    else:
        compressed = changed_xml
    crc = zlib.crc32(changed_xml) & 0xffffffff
    delta = len(compressed) - member.compress_size
    if len(raw) + delta >= 0xffffffff:
        raise ValueError('Result would require ZIP64')
    local_header = bytearray(raw[local:data_start])
    struct.pack_into('<3L', local_header, 14, crc, len(compressed), len(changed_xml))
    directory = bytearray(raw[central_start:end])
    pos = 0
    for info in infos:
        if directory[pos:pos+4] != b'PK\x01\x02':
            raise ValueError('Unexpected ZIP central-directory record')
        nlen, elen, clen = struct.unpack_from('<3H', directory, pos+28)
        original_offset = struct.unpack_from('<L', directory, pos+42)[0]
        if original_offset != info.header_offset:
            raise ValueError('Central-directory member order differs')
        if info.filename == 'Document.xml':
            struct.pack_into('<3L', directory, pos+16, crc, len(compressed), len(changed_xml))
        elif original_offset > local:
            struct.pack_into('<L', directory, pos+42, original_offset+delta)
        pos += 46+nlen+elen+clen
    if pos != len(directory):
        raise ValueError('Unsupported extra central-directory records')
    tail = bytearray(raw[end:])
    struct.pack_into('<L', tail, 16, central_start+delta)
    return (raw[:local] + bytes(local_header) + compressed
            + raw[data_end:central_start] + bytes(directory) + bytes(tail))


def _compressed_member(raw, info):
    nlen, elen = struct.unpack_from('<2H', raw, info.header_offset+26)
    start = info.header_offset+30+nlen+elen
    return raw[start:start+info.compress_size]


def compare_archives(before, after, expected_label):
    attrs = ('filename', 'date_time', 'compress_type', 'comment', 'extra',
             'create_system', 'create_version', 'extract_version', 'reserved',
             'flag_bits', 'volume', 'internal_attr', 'external_attr')
    same, compressed, changed = [], [], []
    with zipfile.ZipFile(io.BytesIO(before)) as a, zipfile.ZipFile(io.BytesIO(after)) as b:
        if a.namelist() != b.namelist() or a.comment != b.comment:
            raise ValueError('ZIP member list, order or archive comment changed')
        for original, result in zip(a.infolist(), b.infolist()):
            if any(getattr(original, k) != getattr(result, k) for k in attrs):
                raise ValueError('ZIP member attributes changed: '+original.filename)
            aa, bb = a.read(original), b.read(result)
            if aa != bb:
                changed.append(original.filename)
            if original.filename != 'Document.xml':
                if aa != bb or (original.CRC, original.file_size, original.compress_size) != (result.CRC, result.file_size, result.compress_size):
                    raise ValueError('Non-document ZIP member changed: '+original.filename)
                ca, cb = _compressed_member(before, original), _compressed_member(after, result)
                if ca != cb:
                    raise ValueError('Non-document compressed bytes changed: '+original.filename)
                same.append([original.filename, sha(aa)])
                compressed.append([original.filename, sha(ca)])
        old_xml, new_xml = a.read('Document.xml'), b.read('Document.xml')
        expected, delta = replace_label_xml(old_xml, expected_label)
        if new_xml != expected or changed not in ([], ['Document.xml']):
            raise ValueError('Archive differs beyond the expected root Label value')
        normal_a = replace_label_xml(old_xml, '__DOCUMENT_LABEL__')[0]
        normal_b = replace_label_xml(new_xml, '__DOCUMENT_LABEL__')[0]
        if normal_a != normal_b:
            raise ValueError('Label-normalized XML differs')
        aggregate = lambda rows: sha(json.dumps(sorted(rows), ensure_ascii=False, separators=(',', ':')).encode())
        return {'field': 'Document.xml / Document / Properties / Property[name=Label] / String@value',
                **delta, 'member_count': len(a.infolist()), 'changed_members': changed,
                'unchanged_member_count': len(same), 'member_order_preserved': True,
                'member_attributes_preserved': list(attrs), 'archive_comment_preserved': True,
                'all_other_uncompressed_members_identical': True,
                'all_other_compressed_members_identical': True,
                'aggregate_format': 'SHA-256 of UTF-8 compact JSON: sorted [member_name, member_sha256] pairs, excluding Document.xml',
                'unchanged_members_aggregate_sha256': aggregate(same),
                'unchanged_compressed_members_aggregate_sha256': aggregate(compressed),
                'source_xml_sha256': sha(old_xml), 'output_xml_sha256': sha(new_xml),
                'label_normalized_xml_sha256': sha(normal_a), 'label_normalized_xml_equal': True,
                'gui_document_sha256': sha(a.read('GuiDocument.xml')),
                'source_sha256': sha(before), 'output_sha256': sha(after)}


def preserve_document_label(source, output, label):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or output.exists():
        raise ValueError('Output must be a new path distinct from the immutable source')
    before = source.read_bytes()
    with zipfile.ZipFile(io.BytesIO(before)) as archive:
        changed_xml, _ = replace_label_xml(archive.read('Document.xml'), label)
    after = _rewrite_document_member(before, changed_xml)
    proof = compare_archives(before, after, label)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(after)
    if sha(source.read_bytes()) != proof['source_sha256'] or sha(output.read_bytes()) != proof['output_sha256']:
        raise ValueError('Source or output changed during label restoration')
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = preserve_document_label(args.source, args.output, args.label)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
