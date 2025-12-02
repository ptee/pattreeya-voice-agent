# Frontend Deployment Guide

This guide shows how to deploy the Pattreeya Voice Assistant frontend to the cloud.

## Prerequisites

- Node.js 18+ and pnpm installed
- LiveKit Cloud account with credentials
- Deployed backend API (or local backend running)

## Environment Files

The frontend uses environment files for configuration:

- **`.env.local`** - Local development (overrides all others)
- **`.env.development`** - Development environment variables
- **`.env.production`** - Production environment variables
- **`.env.example`** - Template for new setups

## Key Environment Variables

```env
# LiveKit Connection
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud

# Backend API Endpoint
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://your-api.com/api/connection-details

# Optional
OPENAI_API_KEY=sk-...
```

## Deployment Options

### Option 1: Deploy to Vercel (Recommended)

Vercel is optimized for Next.js applications.

#### Step 1: Prepare Code

```bash
cd web

# Ensure .env.production is configured correctly
# Update NEXT_PUBLIC_CONN_DETAILS_ENDPOINT to your backend URL
```

#### Step 2: Push to GitHub

```bash
git add .
git commit -m "Frontend ready for cloud deployment"
git push origin main
```

#### Step 3: Deploy on Vercel

1. Go to https://vercel.com
2. Click "Add New..." > "Project"
3. Import your GitHub repository
4. Configure environment variables:
   - `NEXT_PUBLIC_LIVEKIT_URL`
   - `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT`
   - `OPENAI_API_KEY` (optional)
5. Click "Deploy"

Your frontend will be live at `https://your-app.vercel.app`

#### Step 4: Update Backend Configuration

Update your backend API endpoint in Vercel environment variables:

```
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://your-api-domain.com/api/connection-details
```

---

### Option 2: Deploy with Docker

Deploy the frontend in a Docker container.

#### Step 1: Build Docker Image

```bash
docker build -t pattreeya-frontend .
```

#### Step 2: Run Container

```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud \
  -e NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://your-api.com/api/connection-details \
  pattreeya-frontend
```

#### Step 3: Deploy on Cloud Platform

- **AWS**: ECS, ECR, App Runner
- **Google Cloud**: Cloud Run, GKE
- **Azure**: Container Instances, App Service
- **DigitalOcean**: App Platform, Droplets
- **Render**: Deploy from Docker image
- **Railway**: Connect GitHub repo

---

### Option 3: Deploy on a VPS with Nginx Reverse Proxy

For complete control over your infrastructure.

#### Step 1: Build Next.js

```bash
cd web
pnpm install
pnpm build
```

#### Step 2: Copy to Server

```bash
scp -r .next node_modules package.json user@server:/var/www/pattreeya/
```

#### Step 3: Start Node Server

```bash
cd /var/www/pattreeya
pnpm start
```

#### Step 4: Configure Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8019;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### Step 5: Enable SSL (Let's Encrypt)

```bash
certbot certonly --nginx -d yourdomain.com
certbot renew --dry-run  # Test auto-renewal
```

---

## Local Development

### Run Locally with Hot Reload

```bash
cd web

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

Visit http://localhost:3000

### Configure for Local Backend

Update `web/.env.local`:

```env
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details
```

---

## Troubleshooting

### Connection to Backend Fails

**Issue**: "Failed to fetch connection details"

**Solution**:

1. Verify backend is running and accessible
2. Check `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT` is correct
3. Ensure CORS is enabled on backend
4. Check browser console for detailed error

### JWT Invalid Error

**Issue**: "Invalid JWT" when connecting to LiveKit

**Solution**:

1. Verify API credentials in backend match LiveKit Cloud
2. Check that tokens are being generated correctly
3. Ensure token has proper LiveKit claims

### Frontend Build Fails on Deployment

**Issue**: Build errors during deployment

**Solution**:

1. Check Node.js version (18+)
2. Verify all dependencies are installed
3. Look for TypeScript errors: `pnpm type-check`
4. Check environment variables are set

---

## Security Notes

⚠️ **Never commit `.env.local` to version control**

- Add to `.gitignore`
- Use platform-specific secrets management
- Rotate API keys regularly

✅ **Best Practices**:

- Use environment variables for sensitive data
- Enable HTTPS/WSS for all connections
- Set restrictive CORS policies
- Monitor deployment logs
- Use strong API keys

---

## Performance Optimization

### Vercel

- Automatic image optimization
- Edge network caching
- Deploy previews on every commit
- Analytics and monitoring included

### Docker/VPS

```bash
# Build optimized image
docker build -t pattreeya:latest --build-arg NEXT_PUBLIC_LIVEKIT_URL=... .

# Use smaller base image
FROM node:18-alpine

# Enable gzip compression in nginx
gzip on;
gzip_types text/plain application/json;
```

---

## Next Steps

1. **Choose your deployment platform** (Vercel recommended)
2. **Update environment variables** with your LiveKit Cloud credentials
3. **Configure backend API endpoint** for your deployed backend
4. **Test connection** to ensure frontend can reach backend
5. **Monitor logs** after deployment

For more help, see:

- [Vercel Deployment Docs](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/learn/deployment)
- [LiveKit Documentation](https://docs.livekit.io)
