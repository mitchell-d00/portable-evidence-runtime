# Threat Model

**Protected boundary:** deterministic retrieval and integrity relative to an independently known expected root, not authenticity of all historical records.

| Threat | Demonstration behavior | Not claimed |
|---|---|---|
| One record altered, digest unchanged | Refuse / integrity_error | Reliable attribution of attacker |
| Policy bytes altered | Refuse / integrity_error | Policy was legitimate when drafted |
| Capsule root altered | Refuse / integrity_error | Cryptographic identity of producer |
| All content and digests changed coherently | **Only external expected root detects substitution** | Protection if attacker can also replace the trusted root |
| Two eligible owners | Refuse / ambiguous | Automatic resolution of conflicting human evidence |
| Retired / blocked / machine-only claim | Ineligible | Independent truth evaluation |
| Missing expected key | Refuse | Answering via semantic inference |
| Host or browser modified | Outside reference trust boundary | Host compromise resistance |
| Network unavailable | No network dependency for standalone HTML | Compatibility on every browser or device |
| Sensitive data leaked through file copy | Outside reference threat model | Encryption, access management, lawful disclosure |

The archive has two distinct data formats. Root `index.html` demonstrates local source authoring, not independently pinned aggregate authentication. The strict `web/index.html` refuses without a matching independently supplied expected root. A SHA-256 string stored in the same untrusted file cannot be treated as independent evidence of authenticity.
