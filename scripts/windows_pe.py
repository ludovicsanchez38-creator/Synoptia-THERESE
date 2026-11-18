"""Identité des octets PE hors Authenticode, sans validation cryptographique."""
import hashlib


def pe_layout(raw: bytes) -> tuple[int, int, int]:
    """Champs modifiés par Authenticode et fin des en-têtes/sections physiques."""
    if len(raw) < 0x40 or raw[:2] != b'MZ':
        raise ValueError('En-tête PE illisible')
    header = int.from_bytes(raw[0x3c:0x40], 'little')
    optional = header + 24
    if header < 0x40 or raw[header:header + 4] != b'PE\0\0' or len(raw) < optional + 2:
        raise ValueError('En-tête PE illisible')
    magic = int.from_bytes(raw[optional:optional + 2], 'little')
    if magic not in (0x10b, 0x20b):
        raise ValueError('En-tête PE illisible')
    checksum = optional + 64
    security = optional + (112 if magic == 0x20b else 96) + 4 * 8
    if len(raw) < security + 8:
        raise ValueError('En-tête PE illisible')
    count = int.from_bytes(raw[header + 6:header + 8], 'little')
    optional_size = int.from_bytes(raw[header + 20:header + 22], 'little')
    table = optional + optional_size
    end = table + count * 40
    if ((optional_size or count) and table < security + 8) or end > len(raw):
        raise ValueError('Table des sections PE tronquée')
    mapped_end = max(security + 8, end, int.from_bytes(raw[optional + 60:optional + 64], 'little'))
    for index in range(count):
        section = table + index * 40
        size = int.from_bytes(raw[section + 16:section + 20], 'little')
        pointer = int.from_bytes(raw[section + 20:section + 24], 'little')
        if size:
            mapped_end = max(mapped_end, pointer + size)
    if mapped_end > len(raw):
        raise ValueError('Section PE hors du fichier')
    return checksum, security, mapped_end


def neutralize_pe_fields(raw: bytes) -> bytes:
    """Neutraliser checksum et entrée Security, même dans le seul stub d'un PE signé."""
    checksum, security, _ = pe_layout(raw)
    body = bytearray(raw)
    body[checksum:checksum + 4] = bytes(4)
    body[security:security + 8] = bytes(8)
    return bytes(body)


def authenticode_signed(raw: bytes) -> bool:
    """Le PE déclare une table, sans présumer de sa validité ni de son signataire."""
    _, security, _ = pe_layout(raw)
    return any(raw[security:security + 8])


def unsigned_pe_body(raw: bytes) -> bytes:
    """Retirer uniquement la table finale, après contrôle de ses bornes et sections."""
    _, security, mapped_end = pe_layout(raw)
    offset = int.from_bytes(raw[security:security + 4], 'little')
    size = int.from_bytes(raw[security + 4:security + 8], 'little')
    if offset or size:
        if not offset or not size or offset % 8 or offset < mapped_end or offset + size != len(raw):
            raise ValueError('Table de certificats PE hors limites ou chevauchant une section')
        raw = raw[:offset]
    return neutralize_pe_fields(raw)


def unsigned_pe_digest(raw: bytes) -> str | None:
    """Contrôle PE existant partagé avec NSIS ; alignement Authenticode à 8 octets."""
    try:
        body = unsigned_pe_body(raw)
    except ValueError:
        return None
    return hashlib.sha256(body + bytes(-len(body) % 8)).hexdigest()
