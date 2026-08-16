# Security Policy

## Supported versions

This project is pre-1.0 and currently in active design/development. Security fixes will target the latest `main` branch.

## Reporting a vulnerability

Please report vulnerabilities using GitHub's private security advisory feature:

1. Open the repository on GitHub.
2. Select the **Security** tab.
3. Choose **Report a vulnerability**.

If that option is unavailable, contact the repository owner through a private GitHub message.

Do not open a public issue for a suspected vulnerability.

## Security expectations

- Model API keys must be supplied through environment variables or a local secret manager.
- Do not commit `.env` files.
- Web content is untrusted input.
- Tool output must never be interpreted as system instructions.
- Guardrail decisions and unsafe-input handling must be logged.
- Page fetching must use timeouts and response-size limits.

## Scope

The project is not yet production-ready. It should not be used as a safety-critical system until it has completed the security review milestone in the design specification.
