# Security Policy

## Reporting a Vulnerability

The AFRP team takes security vulnerabilities seriously, especially given the
financial reasoning domain of this platform.

**Please do NOT file public GitHub issues for security vulnerabilities.**

### Private disclosure (preferred)

Use [GitHub Security Advisories](https://github.com/mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM/security/advisories/new)
to report vulnerabilities privately. This allows us to:
- Assess impact before public disclosure
- Prepare a fix and release
- Coordinate disclosure timing

### What to include

Please provide:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested remediation (optional)
- CVE reference (if already assigned)

### Response timeline

| Action | Target |
|--------|--------|
| Acknowledge receipt | Within 48 hours |
| Initial assessment | Within 5 business days |
| Patch or mitigation | Within 30 days for high/critical |
| Public disclosure | Coordinated with reporter |

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch | ✅ Active |
| Latest release tag | ✅ Active |
| Older release tags | ❌ No backports |

---

## Security Automation

AFRP uses automated security tooling on every PR and weekly:

| Tool | Purpose |
|------|---------|
| [CodeQL](https://codeql.github.com/) | Static application security testing |
| [pip-audit](https://pypi.org/project/pip-audit/) | Vulnerable dependency detection |
| [Bandit](https://bandit.readthedocs.io/) | Python SAST |
| [TruffleHog](https://github.com/trufflesecurity/trufflehog) | Secret scanning |
| [Dependabot](https://docs.github.com/en/code-security/dependabot) | Dependency updates |
| GitHub Secret Scanning | Native secret detection |

Security findings that reach HIGH severity or above **block merges**.

---

## Threat Model

AFRP is a financial reasoning platform. Priority threat categories:

1. **Data integrity** — Market data and model outputs must not be tampered with
2. **Model poisoning** — Adversarial inputs to the reasoning pipeline
3. **Dependency supply chain** — Malicious or vulnerable third-party packages
4. **Secrets in code** — API keys, HMAC secrets, credentials
5. **Unauthorized access** — Access to governance artifacts

---

## Disclosure Policy

We follow [responsible disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure).
We will credit reporters (with their consent) in release notes and security advisories.
