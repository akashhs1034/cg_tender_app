# Secret scanning

OPPORTA uses Gitleaks with the repository policy in `.gitleaks.toml`. The
configuration extends the upstream rules and has one narrow category allowance:
Supabase publishable keys. Those keys are designed for public clients; their
safety still depends on grants and row-level security.

## Before committing

Install Gitleaks from its official release channel and verify the published
checksum. From the repository root, scan staged changes with full redaction:

```powershell
gitleaks git --staged --redact=100 --no-banner
```

Scan the current tree:

```powershell
gitleaks dir . --redact=100 --no-banner
```

Do not paste a finding or matched value into chat, an issue, a pull request, or
documentation. If a result may be a real credential:

1. Stop the commit.
2. Notify the credential owner through a restricted channel.
3. Revoke or rotate private credentials at the provider.
4. Review provider access or usage logs.
5. Remove the value from the current tree.
6. Record only category, commit, path, status, date, and non-sensitive notes.

Removing a value from the current tree does not revoke it and does not remove it
from Git history. Any optional history rewrite requires a separate reviewed
incident plan after revocation, coordination, and backup.

## Allowlist policy

Never allowlist an entire source directory or a general credential filename.
Allow only a proven placeholder or public identifier class, scope it to the
smallest detector and pattern, explain why it is public, and review the backend
authorization boundary separately.

See
[HISTORICAL_CREDENTIAL_RESPONSE.md](HISTORICAL_CREDENTIAL_RESPONSE.md) for the
secret-safe historical response ledger.
