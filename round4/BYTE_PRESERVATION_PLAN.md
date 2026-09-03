# Round 4A Git byte-preservation plan

Codex CLI combined logs and JSON event streams may contain CRLF. Before any
formal Round-4 evidence exists, `.gitattributes` therefore defines exact
`-text` rules for the four schema-preflight logs/events, their four future
formal-rating counterparts, and the synthetic probe.

`scripts/build_round4_byte_preflight.py` creates only synthetic CRLF content in
an isolated temporary Git repository, stages it under every governed path
class, performs a clean `checkout-index`, and compares SHA-256 and byte size.
It also checks that Git reports `text: unset` for every path. The frozen record
is `round4/preflight/BYTE_PRESERVATION_PREFLIGHT.json`; the local probe is
`round4/preflight/byte_preservation_probe.log`.

The procedure contains no case, gold, prompt, model response, rating,
calibration, or prior evidence. A mismatch fails closed before protocol freeze.

