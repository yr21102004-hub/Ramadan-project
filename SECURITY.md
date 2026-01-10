# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities very seriously. If you discover a security issue, please bring it to our attention.

### How to Report
Please email security@ramadandecor.com with a description of the issue. A member of our security team will review your report and respond within 24 hours.

### What to Include
- Description of the location and potential impact of the vulnerability.
- A detailed description of the steps required to reproduce the vulnerability (POC scripts, screenshots, and compressed packet captures are all helpful to us).

### Disclosure Policy
- Please do not disclose the vulnerability to the public until we have had a chance to fix it.
- We will notify you when the vulnerability is fixed.

## Security Features Implemented
- **HTTPS/HSTS**: Enforced in production.
- **CSRF Protection**: All forms secured.
- **Secure Headers**: CSP, X-Frame-Options, etc.
- **Authentication**: Bcrypt hashing, 2FA for admins, Rate Limiting.
- **Containerization**: Non-root user, read-only filesystem.
