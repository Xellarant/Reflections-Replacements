# Reflections Replacements

Reviewed content corrections for **Aurora Reflections**, delivered as proposals that become local corrections only after the user chooses **Apply**.

Feed: [reflections-replacements.index](https://raw.githubusercontent.com/Xellarant/Reflections-Replacements/master/reflections-replacements.index)

This feed requires a Reflections build with replacement-proposal support. Adding the feed to an older build does not add that feature or activate the corrections. The initial feed and the app integration are being prepared together.

## How it works

1. Reflections downloads `.aurora-correction` proposals during its normal content update. The startup auto-download preference still controls automatic network activity.
2. Reflections checks the installed source's path and exact SHA-256, the proposal payload, required reference targets, and existing local corrections.
3. Applicable proposals appear for review with their affected source and explanation. Downloading a proposal does not change gameplay content or require a database refresh.
4. **Apply** creates a managed XML correction under `custom/user/local`. The original downloaded source and the proposal cache remain available. Existing local corrections are preserved.
5. The applied XML follows Reflections' existing correction lifecycle: upstream changes are compared with its baseline, and redundant corrections can be retired when accepted upstream. Removing a proposal from this feed does not delete an applied correction.

Applied or dismissed proposal revisions are remembered locally. A new proposal revision can be reviewed separately. Applying a proposal is **local acceptance**, not a claim that the upstream author has accepted the repair; the embedded correction records deliberately remain `review-pending`.

The exact source hash limits each proposal to the reviewed source version. A matching filename with changed contents does not automatically qualify. The initial catalog includes direct and `aurora-sources` aggregate layouts; the Tatsumi correction and the two rarity corrections have only the reviewed direct-layout variant.

## Included corrections

The catalog contains **15 proposals, 27 source-layout variants, and 66 correction records**. These include the ten broken grant/extraction references, duplicate item and feature identities, blank Devout feature grants, invalid equipment-pack price placeholders, three item rarities with a one-letter typo, and the missing repeatability metadata on the 2024 Ability Score Improvement and Skilled feats.

| Proposal | Correction |
| --- | --- |
| Walloping Ammunition | Separate its ID from Adamantine Ammunition. |
| Forgotten Secrets items | Separate two item pairs that share IDs. |
| Arcane Artillery | Keep the individual musketball and remove its duplicate pack declaration. |
| Devout fighter | Give two features distinct IDs and repair the parent's blank grants. |
| Tatsumi | Separate Heartening Breath from Cloudstep and repair the parent grant. |
| 2024 equipment packs | Repair Guard's Light Crossbow reference and remove 29 nonnumeric cost placeholders. |
| Spiritualist | Repair Animate Objects' singular ID spelling. |
| Psion disciplines | Repair Wall of Fire, Cause Fear, Rary's Telepathic Bond, and Banishment references. |
| Imperial | Repair the Poison Spray publisher prefix. |
| Demonbinder | Repair both demon-summoning spell IDs. |
| Stoneheart | Use the Xanathar's Erupting Earth definition. |
| Mordenkainen's Tome rarities | Read "Vert Rare" as Very Rare (Crown of Leadership) and "Lgendary" as Legendary (Rattle of Death). |
| Bestial Armor | Read "unommon" as Uncommon. |
| 2024 Ability Score Improvement | Mark all eight existing definitions as repeatable; retain their IDs, prerequisites, and ability choices. |
| 2024 Skilled | Mark all nine existing definitions as repeatable; retain their IDs, prerequisites, and skill/tool choices. |

The repeatable-feat proposals place `allow duplicate=true` in the managed replacement definitions. They use the existing feat-selection support and do not depend on appending setters. They preserve the numbered variants used by existing characters. Their validation covers proposal application, effective content, and selection availability; editing and save/reload of repeated nested choices remain an application verification task.

The retired Staff of Flowers correction and the optional Farmer background customization are excluded. Farmer's equipment pack is part of the general price-placeholder repair; that does not include the Farmer background customization.

Full correction reasons, authoritative source paths, upstream URLs, and hashes are recorded in [catalog.json](catalog.json). The escaped managed payload retains the original source information, complete baseline, and correction provenance.

The **Wall of Fire** and **Banishment** mappings were reviewed and accepted locally after checking alternatives. They remain inferences about the intended spells, not upstream author confirmations. **Stoneheart's Erupting Earth** mapping follows the maintainer's preference for Xanathar's Guide to Everything. The Princes of the Apocalypse definition remains separate, and author confirmation is still pending.

## Aurora Legacy compatibility

The current Legacy code in the Aurora-Lights repository can download these XML-shaped files through its ordinary index updater. The envelope supplies independent update metadata and a valid `<elements>` root. Its content loader enumerates `.xml` files, so the `.aurora-correction` cache is not loaded as gameplay content. Legacy does not provide Reflections' proposal review or Apply workflow.

This describes the inspected current Legacy implementation. The original historical Aurora Builder binary has not been tested against this feed. Do not rename a proposal to `.xml` or copy its envelope into `user/local`; Reflections extracts and validates the actual managed payload when it applies a correction.

## Maintaining the feed

Use Python 3.10 or newer; no third-party Python packages are needed.

```console
python tools/feed.py validate
python tools/feed.py build-index
```

The proposal documents are the canonical payloads. `catalog.json` contains their human-readable summaries, review reasons, reference prerequisites, source identities, and checksums; it does not duplicate the full source text. `build-index` rebuilds the ordinary subscription index from that catalog and then validates the feed.

To rebuild proposals from a reviewed portable correction bundle with `manifest.json` and its templates:

```console
python tools/feed.py import-bundle /path/to/reviewed-correction-bundle
```

The importer uses only catalog-listed entries with category `repair`, checks every original template hash, normalizes payload line endings to LF, and computes the embedded payload hash over the exact UTF-8 text an XML reader receives. Personal preferences are never imported automatically. It retains variant-specific correction keys and provenance.

Before publishing a change:

- Review the actual source change and reference targets. Keep changes for one authoritative source in one managed payload, including related identity and grant repairs together.
- Add the title, summary, rationale, and any newly referenced external IDs to `catalog.json`. Required IDs must refer to installed content; do not substitute a different edition silently.
- Increment the proposal's revision and its envelope's update version together. Increment the index version when its file list changes. Replacing a proposal's content under the same revision is not the normal release workflow.
- Update source hashes and managed baselines only after reviewing that source revision. Keep accepted local fixes in `review-pending`; use the normal upstream-review lifecycle for retirement.
- Run `validate`, then verify the managed correction with the shared Aurora content evaluator/importer against representative content. The standalone validator checks structure, provenance, requirements, and integrity; it does not simulate gameplay or replace the shared evaluator.

See [FORMAT.md](FORMAT.md) for the envelope contract. Keep source attribution and any existing notices with the payload. The feed supplies local corrections and does not assert upstream authorship or endorsement. No new license is assigned here to the underlying source material.
