# Distribution deck backups

This folder preserves the history used by the current V8 Attrition distribution
deck, without modifying the live source artifacts.

## Historical V1-V7 archive

`historical-v1-v7/history.json` is the primary index for prior deck versions.
It records every available V1-V7 HTML deck, manifest, and version-scoped
aggregate JSON evidence under `historical-v1-v7/v<version>/`.

- Search the registry by version, original path, archived path, or SHA-256.
- V1 is explicitly recorded as `not_found` if no V1 artifact exists in this
  workspace; it is never fabricated.
- Historical copies are immutable. A changed live source produces an error
  instead of silently overwriting an archived version.

## V8 pre-overwrite snapshots

- `backups.json` is the searchable registry. Search it by `archive_id`,
  `deck_sha256`, archive timestamp, or original path.
- Each snapshot has an HTML deck and, when it existed, the matching V8
  manifest from the same point in time.
- `tools/build_distribution_html_v8.py` archives automatically before it
  overwrites a changed V8 deck. Identical deck hashes are not copied again.
- V7 remains the separately frozen source deck; it is not a V8 backup.

Only aggregate internal-analysis artifacts belong here. Do not place employee
rows, identifiers, names, exact compensation, or other restricted data here.
