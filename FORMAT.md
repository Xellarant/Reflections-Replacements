# Proposal format, version 1

Each index entry points to a `.aurora-correction` file in the folder named after the index. The ordinary updater downloads these files without activating content.

```xml
<elements>
  <info>
    <name>Human-readable correction title</name>
    <description>What changes and why.</description>
    <update version="1.0.0">
      <file name="example.aurora-correction"
            url="https://raw.githubusercontent.com/Xellarant/Reflections-Replacements/master/reflections-replacements/example.aurora-correction" />
    </update>
  </info>
  <rr:proposal xmlns:rr="urn:aurora-reflections:replacements:1"
               schema-version="1" id="example" revision="1.0.0">
    <rr:title>Human-readable correction title</rr:title>
    <rr:summary>What changes and why.</rr:summary>
    <rr:variant source-path="collection/source.xml" source-sha256="64_HEX_DIGITS">
      <rr:requires id="ID_EXISTING_EXTERNAL_REFERENCE_TARGET" />
      <rr:payload sha256="64_HEX_DIGITS">ESCAPED_MANAGED_XML</rr:payload>
    </rr:variant>
  </rr:proposal>
</elements>
```

The example's hash and payload placeholders are illustrative and do not form an installable proposal.

## Identities and integrity

- `id` is a stable safe slug. `revision` is also the envelope's ordinary updater version; it is independent of the authoritative source's update version inside the payload.
- `source-path` is a relative authoritative XML path under the content root, outside `user/`. Absolute paths, traversal, and backslashes are not accepted. Additional variants support separately reviewed source layouts.
- `source-sha256` is the SHA-256 of the **original authoritative file's raw bytes**. It is not a normalized XML hash.
- `requires` lists the external IDs needed by the newly repaired references. IDs added or renamed within the same payload do not need external prerequisites. These entries do not download additional source collections.
- `payload` is XML-escaped text containing one complete managed `LocalCorrectionDocument`. The payload's correction block must use the same authoritative source path as its variant. It includes the original baseline and source-specific correction fingerprints.
- The payload hash is SHA-256 over UTF-8 encoding of the **payload text after parsing the envelope**. The publisher normalizes line endings to LF before embedding. Hashing the XML-escaped bytes or the entire envelope produces a different value.
- All seed corrections use `review-pending`. This state belongs to the existing local-correction/upstream lifecycle; downloading a proposal does not count as accepting it locally or upstream.

Only `<info>` and the namespaced `<proposal>` appear directly under the wrapper's `<elements>` root. There are no active root `<element>` or `<append>` definitions, and local-correction metadata is inside escaped payload text. Merely scanning the downloaded cache as ordinary content must not activate a proposal.

## Source changes and user decisions

The app checks integrity and source applicability again when Apply is selected. A changed source, missing prerequisite, invalid payload, unsafe path, or existing local correction requires review instead of silent replacement. Applied and dismissed decisions are tied to the proposal identity/revision and content hash; a changed download cannot reuse a prior approval silently.

Applying materializes a new managed XML file under `user/local`; the cached proposal remains in place for update checks. The resulting XML then follows the shared content library's existing conflict, upstream comparison, and retirement behavior. Feed deletion is not a command to delete an applied local correction.
