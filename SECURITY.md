# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please report it privately:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer directly or use GitHub's private vulnerability reporting
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x    | :white_check_mark: |
| 1.x    | :x:                |

## Security Features

- API Key authentication with role-based access control
- Rate limiting (IP/User/Key level)
- Input sanitization (XSS/SQL injection prevention)
- Content filtering with jailbreak detection
- Permission levels: read / write / admin

## Best Practices

- Keep API keys secure, never commit to git
- Use environment variables for secrets
- Enable rate limiting in production
- Regularly update to latest version
- Review security logs for anomalies