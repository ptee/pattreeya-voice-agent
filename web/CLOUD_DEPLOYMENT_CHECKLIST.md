# Cloud Deployment Checklist

Quick checklist for deploying the Pattreeya Voice Assistant frontend to the cloud.

## Pre-Deployment Checklist

- [ ] Code is committed to GitHub repository
- [ ] All environment files are configured:
  - [ ] `.env.local` - for local development
  - [ ] `.env.production` - for cloud deployment
- [ ] Backend API is deployed and accessible
- [ ] LiveKit Cloud project credentials are ready

## Environment Configuration

### For Vercel Deployment

Update in Vercel project settings:

```
NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://your-backend-url.com/api/connection-details
OPENAI_API_KEY=sk-...
```

### For Docker Deployment

Build command:
```bash
docker build -t pattreeya-frontend . \
  --build-arg NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud \
  --build-arg NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://your-backend-url.com/api/connection-details
```

Run command:
```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud \
  -e NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://your-backend-url.com/api/connection-details \
  pattreeya-frontend
```

## Backend Configuration

Your backend needs to be deployed at an accessible URL. Update the frontend to point to it:

```
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://your-backend.com/api/connection-details
```

### Backend Deployment Options

1. **Same as Agent on LiveKit Cloud**
   - Both agent and API are deployed together
   - Simple configuration

2. **Separate VPS/Server**
   - Use Docker container
   - Set up nginx reverse proxy
   - Configure firewall/CORS

3. **Vercel for Frontend + Custom VPS for Backend**
   - Frontend on Vercel (free)
   - Backend on your VPS
   - Point frontend to backend URL

## Deployment Steps by Platform

### ✅ Vercel (Recommended - 5 minutes)

1. Push code to GitHub
2. Go to https://vercel.com
3. Click "Add New" > "Project"
4. Select your repository
5. Add environment variables
6. Click "Deploy"

### 📦 Docker on Cloud Platform (10-15 minutes)

1. Build Docker image: `docker build -t pattreeya-frontend .`
2. Push to Docker Hub or registry
3. Deploy on: AWS ECS, Google Cloud Run, Azure Container Instances, etc.
4. Configure environment variables in platform dashboard

### 🖥️ VPS with Nginx (20-30 minutes)

1. Build Next.js: `pnpm build`
2. Copy files to server via SCP
3. Install Node.js on server
4. Start with `pnpm start`
5. Configure nginx as reverse proxy
6. Set up SSL certificate with Let's Encrypt

## Testing After Deployment

- [ ] Frontend loads successfully
- [ ] Can connect to LiveKit
- [ ] Can start a voice call
- [ ] Messages appear in chat
- [ ] Agent responds properly

### Quick Test Script

```bash
# Test frontend loads
curl -I https://your-frontend-url.com

# Test backend API is accessible
curl -X POST https://your-backend-url.com/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{"room_config": {"agents": []}}'

# Should return connection details with valid JWT token
```

## Monitoring & Maintenance

- [ ] Set up error logging (Sentry, LogRocket)
- [ ] Enable analytics (Vercel Analytics, Google Analytics)
- [ ] Monitor backend API usage
- [ ] Set up alerts for failures
- [ ] Plan regular backups (if self-hosted)

## Security Checklist

- [ ] Never commit `.env.local` to git
- [ ] Rotate API keys regularly
- [ ] Enable HTTPS/WSS on all connections
- [ ] Set restrictive CORS policies
- [ ] Enable rate limiting on API
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated: `pnpm audit fix`

## Rollback Plan

If deployment has issues:

1. **Vercel**: Revert to previous deployment in Vercel dashboard (1 click)
2. **Docker**: Redeploy previous image version
3. **VPS**: Restart previous version or restore from backup

## Support Resources

- 📖 [Next.js Deployment Docs](https://nextjs.org/learn/deployment)
- 🚀 [Vercel Docs](https://vercel.com/docs)
- 🐳 [Docker Docs](https://docs.docker.com)
- 🎤 [LiveKit Docs](https://docs.livekit.io)

## Common Issues

| Issue | Solution |
|-------|----------|
| 404 not found | Check environment variables are set correctly |
| JWT invalid | Verify backend API credentials match LiveKit Cloud |
| CORS errors | Enable CORS on backend API |
| Slow performance | Check CDN, image optimization, build size |
| Connection timeout | Verify backend URL is accessible, check firewall |

---

**Ready to deploy?** Start with **Vercel** - it's the fastest option! 🚀
