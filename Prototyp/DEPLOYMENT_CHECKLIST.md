
# Koyeb Deployment Checklist for ABS-CDSS

## Pre-deployment (Local)
- [ ] All tests pass locally
- [ ] Docker build succeeds locally
- [ ] Environment variables configured
- [ ] Code committed to main branch

## Koyeb Setup
- [ ] Create new Koyeb app
- [ ] Connect GitHub repository
- [ ] Set environment variables:
  - [ ] NOVITA_API_KEY (secret)
  - [ ] DATABASE_URL (secret) 
  - [ ] All public variables from template
- [ ] Configure build settings:
  - [ ] Build type: Docker
  - [ ] Dockerfile: Dockerfile
  - [ ] Auto-deploy: Enabled (main branch)
- [ ] Set instance type: nano (free tier)

## Database Setup
- [ ] Create PostgreSQL database (recommend: Supabase/Neon)
- [ ] Update DATABASE_URL in Koyeb secrets
- [ ] Test database connection

## Domain & SSL
- [ ] Configure custom domain (optional)
- [ ] SSL automatically provisioned by Koyeb

## Post-deployment
- [ ] Test health endpoint: /health
- [ ] Test admin frontend: /admin
- [ ] Test enduser frontend: /
- [ ] Test API functionality: /docs
- [ ] Upload test guidelines
- [ ] Verify RAG functionality

## Monitoring
- [ ] Check application logs in Koyeb dashboard
- [ ] Monitor resource usage
- [ ] Set up alerts for errors

## URLs after deployment
- Health Check: https://your-app.koyeb.app/health
- API Docs: https://your-app.koyeb.app/docs
- Admin UI: https://your-app.koyeb.app/admin
- End User: https://your-app.koyeb.app/

## Troubleshooting
- Check logs in Koyeb dashboard
- Verify environment variables
- Test database connectivity
- Check Docker build logs
