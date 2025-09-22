# Security Policy

## Supported Versions

We actively support the following versions of GarminTurso:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please:

1. **Email**: Send details to [maintainer-email] (replace with actual email)
2. **Subject**: Use "SECURITY: [Brief Description]" as the subject line
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Suggested fix (if you have one)

### What to Expect

- **Acknowledgment**: We'll acknowledge receipt within 48 hours
- **Initial Response**: We'll provide an initial assessment within 5 business days
- **Updates**: We'll keep you informed of our progress
- **Resolution**: We'll work to resolve the issue promptly
- **Credit**: We'll credit you in the security advisory (unless you prefer anonymity)

### Security Considerations for GarminTurso

#### Sensitive Data
- **Garmin Credentials**: Stored in `.env` file - never commit to version control
- **Authentication Tokens**: Stored locally in `~/.garminconnect/` with restricted permissions (700)
- **Health Data**: Stored locally in SQLite database - ensure proper file permissions

#### API Security
- **Rate Limiting**: Built-in rate limiting to respect Garmin's API limits
- **Token Management**: Automatic token refresh and secure storage
- **MFA Support**: Proper handling of two-factor authentication

#### Best Practices for Users

1. **Environment Files**:
   ```bash
   # Ensure .env is not readable by others
   chmod 600 .env
   ```

2. **Database Security**:
   ```bash
   # Secure database file permissions
   chmod 600 data/garmin.db
   ```

3. **Token Directory**:
   ```bash
   # Secure auth token directory
   chmod 700 ~/.garminconnect/
   ```

4. **Network Security**:
   - All communication with Garmin Connect uses HTTPS
   - No data transmitted to third parties
   - All processing happens locally

#### Known Security Considerations

- **Credentials in Memory**: Credentials may be temporarily stored in memory during authentication
- **Log Files**: Ensure log files don't contain sensitive information
- **Process Listing**: Process arguments may be visible in system process lists

### Security Features

- **Local Storage Only**: No cloud dependencies beyond Garmin Connect
- **Encrypted Communication**: All API calls use HTTPS
- **Token Expiration**: Automatic token refresh prevents stale credentials
- **Error Handling**: Sensitive information redacted from error messages
- **File Permissions**: Proper permissions set on sensitive files

### Scope

This security policy covers:
- GarminTurso application code
- Authentication mechanisms
- Data storage and handling
- API interactions with Garmin Connect

This policy does not cover:
- Security of Garmin Connect itself
- User's system security
- Third-party dependencies (report to respective projects)

### Updates

This security policy may be updated from time to time. Check this file for the latest version.

---

Thank you for helping keep GarminTurso and our users safe!