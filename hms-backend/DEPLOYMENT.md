# HMS Backend - Serverless Deployment Guide

This document provides instructions for deploying the HMS Django backend to AWS Lambda using the Serverless Framework.

## Prerequisites

1. **AWS Account**: You need an AWS account with appropriate permissions
2. **AWS CLI**: Install and configure AWS CLI with your credentials
   ```bash
   aws configure
   ```
3. **Node.js & npm**: Required for Serverless Framework
4. **Serverless Framework**: Install globally
   ```bash
   npm install -g serverless
   ```
5. **Serverless Plugins**: Install required plugins
   ```bash
   cd hms-backend
   npm install --save-dev serverless-wsgi serverless-python-requirements
   ```

## Database Setup

The serverless deployment expects a PostgreSQL database (preferably AWS RDS). Make sure to:

1. Create an RDS PostgreSQL instance
2. Configure security groups to allow Lambda access
3. Update environment variables with database credentials

## Environment Variables

Create a `.env` file or configure these in AWS Systems Manager Parameter Store:

```bash
# Django
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=*

# Database
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-api-gateway-url/api/accounts/auth/google/callback/
```

## Deployment Commands

### Deploy to Development
```bash
cd hms-backend
serverless deploy --stage dev
```

### Deploy to Production
```bash
serverless deploy --stage prod
```

### Deploy to Specific Region
```bash
serverless deploy --region us-west-2
```

## Post-Deployment Steps

1. **Run Migrations**: After first deployment, run Django migrations
   ```bash
   serverless invoke -f api --data '{"command": "migrate"}'
   ```
   Or connect to your RDS and run migrations manually

2. **Collect Static Files**: For production
   ```bash
   python manage.py collectstatic --noinput
   ```
   Upload static files to S3 and configure CloudFront

3. **Create Superuser**: Create admin user
   ```bash
   # Connect to RDS and run
   python manage.py createsuperuser
   ```

## API Endpoint

After deployment, Serverless will output your API Gateway endpoint:
```
https://xxxxxxxxxx.execute-api.region.amazonaws.com/dev/
```

Update your frontend's API base URL to this endpoint.

## Monitoring & Logs

View logs:
```bash
serverless logs -f api --tail
```

## Troubleshooting

### Cold Start Issues
- Increase Lambda memory (currently 512MB)
- Use provisioned concurrency for production

### Database Connection Issues
- Check security groups allow Lambda to RDS connection
- Verify VPC configuration
- Use RDS Proxy for better connection management

### Package Size Too Large
- The configuration uses layers for Python requirements
- Further optimize by removing unused dependencies

## Cost Optimization

1. **Use RDS Proxy**: Reduces database connections
2. **API Gateway Caching**: Cache GET requests
3. **Lambda Provisioned Concurrency**: Only for production if needed

## Cleanup

Remove all deployed resources:
```bash
serverless remove --stage dev
```

## Notes

- Static files (STATIC_ROOT) and media files (MEDIA_ROOT) should be served from S3
- Consider using AWS ElastiCache for session storage in production
- Use AWS Secrets Manager for sensitive credentials instead of environment variables
