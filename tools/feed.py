#!/usr/bin/env python3
"""Build and validate the Reflections Replacements feed (Python 3.10+, stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog.json"
BASE = "https://raw.githubusercontent.com/Xellarant/Reflections-Replacements/master/"
INDEX = "reflections-replacements.index"
FOLDER = "reflections-replacements"
NS = "urn:aurora-reflections:replacements:1"
LOCAL_NS = "urn:aurora-lights:corrections:1"
ET.register_namespace("rr", NS)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def parse(text: str) -> ET.Element:
    require("<!DOCTYPE" not in text.upper() and "<!ENTITY" not in text.upper(), "DTD/entities are not allowed")
    return ET.fromstring(text)


def text_file(path: Path) -> str:
    # XML normalizes literal CR/LF line endings. Hash the payload as a reader sees it.
    return path.read_text(encoding="utf-8-sig")


def write_xml(path: Path, root: ET.Element) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write('<?xml version="1.0" encoding="utf-8"?>\n')
        output.write(ET.tostring(root, encoding="unicode"))
        output.write("\n")


def read_catalog() -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    require(catalog["schemaVersion"] == 1, "Unknown catalog schema")
    ids = [entry["id"] for entry in catalog["entries"]]
    require(len(ids) == len(set(ids)), "Duplicate catalog ID")
    require(all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", id_) for id_ in ids), "Unsafe catalog ID")
    return catalog


def proposal_path(entry: dict) -> Path:
    return ROOT / FOLDER / (entry["id"] + ".aurora-correction")


def write_index(catalog: dict) -> None:
    root = ET.Element("index")
    info = ET.SubElement(root, "info")
    ET.SubElement(info, "name").text = "Reflections Replacements"
    ET.SubElement(info, "description").text = "Reviewed correction proposals; downloading never applies them."
    update = ET.SubElement(info, "update", version=catalog["version"])
    ET.SubElement(update, "file", name=INDEX, url=BASE + INDEX)
    files = ET.SubElement(root, "files")
    for entry in catalog["entries"]:
        filename = proposal_path(entry).name
        ET.SubElement(files, "file", name=filename, url=BASE + FOLDER + "/" + filename)
    write_xml(ROOT / INDEX, root)


def checked_source_path(value: str) -> None:
    path = PurePosixPath(value)
    require(value and "\\" not in value and ":" not in value and not path.is_absolute(), "Unsafe source path: " + value)
    require(all(part not in ("", ".", "..") for part in value.split("/")), "Unsafe source path: " + value)
    require(path.suffix == ".xml" and path.parts[0].lower() != "user", "Source must be an authoritative XML: " + value)


def checked_payload(payload: str, source_path: str) -> ET.Element:
    root = parse(payload)
    require(root.tag == "elements", "Payload must be an elements document")
    blocks = root.findall("{" + LOCAL_NS + "}corrections")
    require(len(blocks) == 1, "Payload needs exactly one local-correction block")
    block = blocks[0]
    require(block.get("version") == "1" and block.get("source-path") == source_path, "Payload provenance mismatch")
    baseline = block.find("{" + LOCAL_NS + "}baseline")
    require(baseline is not None and baseline.get("encoding") == "escaped-xml", "Missing escaped baseline")
    parse(baseline.text or "")
    corrections = block.findall("{" + LOCAL_NS + "}correction")
    require(bool(corrections), "Empty correction list")
    require(all(c.get("state") == "review-pending" for c in corrections), "Public proposals must remain review-pending")
    require(all(c.get("operation") in ("add", "remove", "replace", "rename") for c in corrections), "Unknown correction operation")
    require(len({c.get("key") for c in corrections}) == len(corrections), "Duplicate correction key")
    return root


def import_bundle(bundle: Path, catalog: dict) -> None:
    """Import only catalog-listed, reviewed repairs; never personal preferences."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8-sig"))
    entries = {entry["id"]: entry for entry in manifest["entries"]}
    for entry in catalog["entries"]:
        source = entries[entry["id"]]
        require(source["category"] == "repair", "Only reviewed repairs can enter this feed")
        root = ET.Element("elements")
        info = ET.SubElement(root, "info")
        ET.SubElement(info, "name").text = entry["title"]
        ET.SubElement(info, "description").text = entry["summary"]
        update = ET.SubElement(info, "update", version=entry["revision"])
        filename = proposal_path(entry).name
        ET.SubElement(update, "file", name=filename, url=BASE + FOLDER + "/" + filename)
        proposal = ET.SubElement(root, "{" + NS + "}proposal", {"schema-version": "1", "id": entry["id"], "revision": entry["revision"]})
        ET.SubElement(proposal, "{" + NS + "}title").text = entry["title"]
        ET.SubElement(proposal, "{" + NS + "}summary").text = entry["summary"]
        provenance = []
        for variant in source["variants"]:
            source_path = variant["sourcePath"]
            checked_source_path(source_path)
            template = (bundle / variant["template"]).resolve()
            require(template.is_relative_to(bundle.resolve()), "Template escapes bundle")
            require(digest(template.read_bytes()) == variant["templateSha256"], "Template hash mismatch: " + str(template))
            payload = text_file(template)
            parsed = checked_payload(payload, source_path)
            payload_hash = digest(payload.encode("utf-8"))
            node = ET.SubElement(proposal, "{" + NS + "}variant", {"source-path": source_path, "source-sha256": variant["sourceSha256"]})
            for target in entry["requires"]:
                ET.SubElement(node, "{" + NS + "}requires", id=target)
            ET.SubElement(node, "{" + NS + "}payload", sha256=payload_hash).text = payload
            origin = parsed.find("info/update/file")
            keys = [c.get("key") for c in parsed.findall("{" + LOCAL_NS + "}corrections/{" + LOCAL_NS + "}correction")]
            provenance.append({"sourcePath": source_path, "sourceSha256": variant["sourceSha256"], "payloadSha256": payload_hash, "upstreamUrl": origin.get("url") if origin is not None else None, "correctionKeys": keys})
        entry["variants"] = provenance
        entry["corrections"] = source["corrections"]
        write_xml(proposal_path(entry), root)
    catalog["importedFrom"] = {"bundleVersion": manifest["version"], "contentLibrary": manifest["contentLibrary"]}
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_index(catalog)


def validate(catalog: dict) -> dict:
    index = parse(text_file(ROOT / INDEX))
    require(index.tag == "index", "Feed root must be index")
    own_file = index.find("info/update/file")
    require(own_file is not None and own_file.get("name") == INDEX and own_file.get("url") == BASE + INDEX, "Incorrect index updater identity")
    require(index.find("info/update").get("version") == catalog["version"], "Index version differs from catalog")
    actual_files = {(f.get("name"), f.get("url")) for f in index.findall("files/file")}
    expected_files = {(proposal_path(e).name, BASE + FOLDER + "/" + proposal_path(e).name) for e in catalog["entries"]}
    require(actual_files == expected_files and len(index.findall("files/file")) == len(expected_files), "Index entries differ from catalog")
    require({p.name for p in (ROOT / FOLDER).iterdir()} == {name for name, _ in expected_files}, "Unexpected files in proposal cache folder")
    variants, records = 0, 0
    for entry in catalog["entries"]:
        envelope = parse(text_file(proposal_path(entry)))
        require(envelope.tag == "elements", "Proposal wrapper must be elements")
        require([n.tag for n in envelope] == ["info", "{" + NS + "}proposal"], "Proposal has active content or unexpected root nodes")
        proposal = envelope.find("{" + NS + "}proposal")
        require(proposal.attrib == {"schema-version": "1", "id": entry["id"], "revision": entry["revision"]}, "Proposal identity mismatch")
        for field in ("title", "summary"):
            require(proposal.findtext("{" + NS + "}" + field) == entry[field], "Proposal " + field + " differs from catalog")
        update = envelope.find("info/update")
        require(update is not None and update.get("version") == entry["revision"], "Updater revision must match proposal revision")
        own_file = update.find("file")
        require(own_file is not None and (own_file.get("name"), own_file.get("url")) in expected_files and own_file.get("name") == proposal_path(entry).name, "Incorrect proposal updater identity")
        nodes = proposal.findall("{" + NS + "}variant")
        require(len(nodes) == len(entry["variants"]), "Variant count mismatch")
        require(len({v.get("source-path") for v in nodes}) == len(nodes), "Duplicate source-path variant")
        for variant, expected in zip(nodes, entry["variants"]):
            source_path = variant.get("source-path", "")
            checked_source_path(source_path)
            require(source_path == expected["sourcePath"], "Source path differs from catalog")
            require(variant.get("source-sha256") == expected["sourceSha256"] and bool(re.fullmatch("[0-9A-F]{64}", expected["sourceSha256"])), "Invalid source hash")
            require([r.get("id") for r in variant.findall("{" + NS + "}requires")] == entry["requires"], "Required IDs differ from catalog")
            payload = variant.find("{" + NS + "}payload")
            require(payload is not None and not list(payload), "Payload must be escaped XML text")
            require(digest((payload.text or "").encode("utf-8")) == payload.get("sha256") == expected["payloadSha256"], "Parsed payload hash mismatch")
            parsed = checked_payload(payload.text or "", source_path)
            referenced_ids = {n.get("id") for n in parsed.findall(".//grant")} | {(n.text or "").strip() for n in parsed.findall(".//extract/item")}
            require(set(entry["requires"]).issubset(referenced_ids), "A required ID is not referenced by the corrected content")
            corrections = parsed.findall("{" + LOCAL_NS + "}corrections/{" + LOCAL_NS + "}correction")
            require(len(corrections) == len(entry["corrections"]), "Correction count differs from catalog")
            require([c.get("key") for c in corrections] == expected["correctionKeys"], "Correction identities differ from catalog")
            variants += 1
        records += len(entry["corrections"])
    return {"proposals": len(catalog["entries"]), "sourceVariants": variants, "correctionRecords": records, "requiredExternalIds": len({r for e in catalog["entries"] for r in e["requires"]})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("build-index")
    importer = sub.add_parser("import-bundle")
    importer.add_argument("bundle", type=Path)
    args = parser.parse_args()
    catalog = read_catalog()
    if args.command == "import-bundle":
        import_bundle(args.bundle, catalog)
    elif args.command == "build-index":
        write_index(catalog)
    print(json.dumps(validate(catalog), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, ET.ParseError) as error:
        sys.exit("Feed validation failed: " + str(error))
