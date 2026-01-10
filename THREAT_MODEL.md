# Threat Model for Ramadan Decor App

## 1. System Overview
Web application for a decor company allowing users to view services, projects, and contact the company. Includes an Admin Dashboard for managing potential clients and messages.

## 2. Assets (What we are protecting)
1.  **Client Data**: Names, Phone Numbers, Project Descriptions (High Sensitivity).
2.  **Admin Access**: Control over the entire platform (Critical).
3.  **Application Integirty**: Preventing defacement or malicious code injection.
4.  **Availability**: Ensuring the site is up for legitimate customers.

## 3. Threat Analysis (STRIDE)

| Threat Type | Potential Scenario | Mitigation Implemented |
| :--- | :--- | :--- |
| **Spoofing** | Attacker impersonating Admin. | **2FA (TOTP)**, **Secure Session Cookies**. |
| **Tampering** | Modifying user data or injecting scripts (XSS). | **CSP (Talisman)**, **Input Sanitization (Bleach)**, **Read-only Containers**. |
| **Repudiation** | Admin performs action (e.g., delete user) and denies it. | **Audit Logs** (logs Actor, Action, Target). |
| **Information Disclosure** | leaking stack traces or server info. | **Custom 404/500 Pages**, **Hiding Server Headers**, **Vague Error Messages**. |
| **Denial of Service** | Bot flooding login or contact forms. | **Rate Limiting**, **Math CAPTCHA**, **Docker Resource Limits**, **Infrastructure resource limits**. |
| **Elevation of Privilege** | Normal user accessing Admin dashboard. | **Role-Based Access Control (RBAC)** checks on every admin route. |

## 4. Supply Chain & Build Security
- **Risk**: Malicious dependency.
- **Mitigation**: `safety` checks in build pipeline, pinning versions in `requirements.txt`.

## 5. Bot Management
- **Risk**: Scrapers and Spammers.
- **Mitigation**: Honeypot fields in forms, Rate Limiting, User-Agent filtering (planned).

## 6. Future Enhancements
- External WAF (Cloudflare) is recommended for production.
- PERIODIC Penetration Testing.
