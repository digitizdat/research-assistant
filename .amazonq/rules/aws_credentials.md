# AWS Credentials for Development

When performing work that requires access to AWS services, always check the root directory of this repository for the `session-environment.sh` file, which contains the most recent AWS credentials.

## Usage
```bash
source session-environment.sh
```

## Credentials Available
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_SESSION_TOKEN

Use these credentials for any AWS service operations during development and testing.