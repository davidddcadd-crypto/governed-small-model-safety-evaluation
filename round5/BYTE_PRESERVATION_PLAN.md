# Round 5A exact-byte preservation plan

Codex combined logs and JSON event streams may contain CRLF. Before formal
evidence exists, scoped `round5/.gitattributes` and
`results/round5_granite4_3b/.gitattributes` files therefore define targeted
`-text` rules only for Round-5 schema-preflight, future formal-rating, and
synthetic-probe path classes. The frozen root `.gitattributes` remains byte
identical to the Round-4 publication baseline.

`scripts/build_round5_byte_preflight.py` uses synthetic CRLF content in an
isolated temporary Git repository, stages every governed path, performs a clean
`checkout-index`, checks Git reports `text: unset`, and compares size and
SHA-256. It creates `round5/preflight/byte_preservation_probe.log` and
`round5/preflight/BYTE_PRESERVATION_PREFLIGHT.json`. The procedure contains no
case, gold, prompt, model response, rating, calibration, or prior evidence.
Any mismatch fails closed before the Round-5 manifest freeze.
