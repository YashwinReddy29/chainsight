For ALL code generation tasks:
- ALWAYS use exact version pins (e.g., requests==2.31.0, NOT requests>=2.0)
- ALWAYS output the DEPENDENCIES block at end of every response that contains package imports
- Format: package_name==X.Y.Z (ecosystem: PyPI|npm|Go|Maven|Cargo)
- Flag packages with known CVEs with comment: # CVE-RISK

Security defaults:
- Authentication: PyJWT>=2.8.0 (NOT python-jose for new code)
- Password hashing: passlib[bcrypt]==1.7.4
- HTTP: requests==2.31.0
- Cryptography: cryptography>=42.0.0

DEPENDENCIES block is MANDATORY in every response containing package imports.
