# Contributing & Security Policy

## separation of Duties (SoD)

To ensure the security and integrity of the application, we enforce the following separation of duties:

1.  **Developers**: Write code, run local tests. CANNOT deploy directly to production.
2.  **Security Reviewer**: Reviews the code changes, checks security scan results (`run_security_scan.py`), and approves PRs.
3.  **DevOps/Admin**: Manages the deployment pipeline and server infrastructure. Access to production keys/secrets.

## Deployment Process (Secure SDLC)

1.  **Development**:
    - Write code.
    - Run `python run_security_scan.py` locally.
    - Commit changes.

2.  **Code Review**:
    - Create a Pull Request.
    - Manual review for logic errors.
    - Automated check for vulnerabilities.

3.  **Staging**:
    - Deploy to a staging environment (Mirror of prod).
    - Functional testing.

4.  **Production**:
    - Authorized personnel trigger deployment.
    - Infrastructure is immutable (Docker containers are replaced, not modified).

## Rules
- **NEVER** commit secrets to Git.
- **NEVER** turn on Debug Mode in Production (`FLASK_DEBUG=false`).
- All libraries must be vetted before addition.
