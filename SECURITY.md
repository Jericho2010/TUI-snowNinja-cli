# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v0.1.x  | :white_check_mark: |

## Reporting a Vulnerability

We take the security of our users seriously. If you find a security vulnerability, please do not open a public issue. Instead, please follow these steps:

1. Send an email to the project maintainers (see README).
2. Provide a detailed description of the vulnerability and steps to reproduce it.
3. We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Credential Safety

**SnowNinja is designed with a "Security-First" architecture:**
- **No Credentials in Repo**: SnowNinja never stores your Snowflake passwords, Private Keys, or NVIDIA API keys within the repository.
- **External Configuration**: All sensitive configuration is stored locally in `~/.snowninja/config.yaml`. 
- **Encryption**: We recommend ensuring your home directory is encrypted if you are storing production-level credentials.
