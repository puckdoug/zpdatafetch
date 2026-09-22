---
description: Credentials, secrets, and sensitive data protection
globs:
---

# Security Rules

- NEVER write passwords, secrets, tokens, or API keys into any file — not in source code, config files, documentation, CLAUDE.md rules, planning docs, or comments. No exceptions.
- All credentials are stored in the system keyring.
- When a script needs a secret, it must read it from keyring at runtime. Never pass secrets as command-line arguments, embed them in shell scripts, or write them to temporary files.
