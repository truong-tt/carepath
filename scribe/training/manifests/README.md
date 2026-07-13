# Training Dataset Manifests

Every GEC training dataset needs a JSON manifest containing:

- `dataset_id`
- `source_description`
- `consent_status` (`approved` is required to run `--stage train`)
- `sha256` of the immutable dataset export

`vimedcss-v1.json` is intentionally pending owner approval. Replace its
placeholder hash only after the owner has verified lawful source, consent or
other legal basis, and de-identification. Do not add patient audio to this
repository.
