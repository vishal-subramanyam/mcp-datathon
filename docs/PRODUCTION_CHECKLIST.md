# Production Deployment Checklist

Complete this checklist before deploying to production.

## Pre-Deployment

### Code Quality
- [ ] All linting errors resolved
- [ ] Code reviewed and approved
- [ ] No hardcoded secrets or API keys
- [ ] Error handling implemented for all external calls
- [ ] Logging configured appropriately
- [ ] No debug statements or print() calls

### Security
- [ ] All secrets moved to environment variables
- [ ] CORS configured with specific origins (not "*")
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Input validation implemented
- [ ] SQL injection protection (if using SQL)
- [ ] XSS protection implemented
- [ ] HTTPS enforced
- [ ] Trusted host middleware configured

### Configuration
- [ ] Environment set to "production"
- [ ] Debug mode disabled
- [ ] API documentation disabled (or protected)
- [ ] Appropriate log level set (INFO or WARNING)
- [ ] All required environment variables documented
- [ ] Environment variables validated on startup

### Dependencies
- [ ] All dependencies listed in requirements files
- [ ] Dependency versions pinned
- [ ] No development dependencies in production requirements
- [ ] Security vulnerabilities checked (`pip audit`)

## Database (Supabase)

### Setup
- [ ] Supabase project created
- [ ] Schema created (`config/supabase_schema.sql`)
- [ ] Row Level Security (RLS) policies enabled
- [ ] Indexes created for performance
- [ ] Backup strategy configured

### Configuration
- [ ] `SUPABASE_URL` environment variable set
- [ ] `SUPABASE_KEY` environment variable set
- [ ] Connection pooling configured
- [ ] Timeout settings appropriate

### Testing
- [ ] Connection test successful
- [ ] CRUD operations tested
- [ ] RLS policies verified
- [ ] Performance tested under load

## Backend (Render)

### Setup
- [ ] Render account created
- [ ] Service created and connected to Git repository
- [ ] Build command configured: `pip install -r requirements-backend.txt`
- [ ] Start command configured: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- [ ] Health check path set: `/health`
- [ ] Persistent disk configured for flashcard data (if needed)

### Environment Variables
- [ ] `ENVIRONMENT=production`
- [ ] `OPENROUTER_API_KEY` set
- [ ] `SUPABASE_URL` set
- [ ] `SUPABASE_KEY` set
- [ ] `BASE_URL` set (your Render backend URL)
- [ ] `FRONTEND_URL` set (your Streamlit/Vercel URL)
- [ ] `CANVAS_API_URL` set (optional default)
- [ ] `CANVAS_API_KEY` set (optional default)

### Testing
- [ ] Health endpoint returns 200: `GET /health`
- [ ] Readiness endpoint works: `GET /readiness`
- [ ] Liveness endpoint works: `GET /liveness`
- [ ] Metrics endpoint accessible: `GET /metrics`
- [ ] API endpoints tested
- [ ] Error handling verified
- [ ] Response times acceptable

### Monitoring
- [ ] Render logs reviewed
- [ ] Health checks passing
- [ ] No memory leaks detected
- [ ] CPU usage acceptable
- [ ] Response times monitored

## Frontend (Streamlit Cloud)

### Setup
- [ ] Streamlit Cloud account created
- [ ] App created and connected to repository
- [ ] Main file path set: `frontend/app.py`
- [ ] Python version set: 3.11
- [ ] Requirements file recognized: `requirements-frontend.txt`

### Configuration
- [ ] Secrets configured in Streamlit dashboard
- [ ] `API_URL` points to Render backend
- [ ] Custom domain configured (if applicable)

### Testing
- [ ] Frontend loads successfully
- [ ] Backend connection test passes
- [ ] All pages accessible
- [ ] Settings page works
- [ ] Chat functionality working
- [ ] Error messages displayed appropriately
- [ ] Mobile responsiveness checked

## API Keys & Services

### OpenRouter
- [ ] API key obtained
- [ ] Credit/billing configured
- [ ] Rate limits understood
- [ ] Fallback model configured (if primary unavailable)

### Canvas LMS
- [ ] Default API URL configured (if needed)
- [ ] Default API key configured (if needed)
- [ ] Per-user credentials tested

### Google APIs (Optional)
- [ ] Google Cloud project created
- [ ] Calendar API enabled
- [ ] Gmail API enabled
- [ ] OAuth credentials created
- [ ] Redirect URIs configured
- [ ] Scopes appropriate for use case

## Integration Testing

### End-to-End Tests
- [ ] User can access frontend
- [ ] User can enter credentials in Settings
- [ ] Credentials saved to Supabase
- [ ] Canvas integration works
- [ ] Calendar integration works (if configured)
- [ ] Gmail integration works (if configured)
- [ ] Flashcard generation works
- [ ] Error handling works for all services

### Load Testing
- [ ] Concurrent user testing completed
- [ ] Response times under load acceptable
- [ ] No memory leaks under sustained load
- [ ] Rate limiting works as expected

## Performance

### Backend
- [ ] Response times < 2s for most requests
- [ ] p95 response time < 5s
- [ ] No N+1 query problems
- [ ] Caching implemented where appropriate
- [ ] Database queries optimized

### Frontend
- [ ] Page load time < 3s
- [ ] No blocking operations in main thread
- [ ] Assets optimized
- [ ] Error states handled gracefully

## Documentation

### Code Documentation
- [ ] README updated with deployment instructions
- [ ] API endpoints documented
- [ ] Environment variables documented
- [ ] Architecture diagram created/updated

### User Documentation
- [ ] User guide created
- [ ] Setup instructions clear
- [ ] Troubleshooting guide available
- [ ] FAQ updated

### Operations Documentation
- [ ] Deployment process documented
- [ ] Rollback procedure documented
- [ ] Monitoring setup documented
- [ ] Incident response plan created

## Post-Deployment

### Immediate (0-24 hours)
- [ ] Deployment successful
- [ ] All services running
- [ ] Health checks passing
- [ ] No critical errors in logs
- [ ] Test user accounts working
- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify CORS working

### Short-term (1-7 days)
- [ ] Monitor daily active users
- [ ] Review error logs daily
- [ ] Check performance metrics
- [ ] Verify backup system working
- [ ] Test credential recovery
- [ ] Monitor API usage/costs

### Long-term (ongoing)
- [ ] Weekly log review
- [ ] Monthly security audit
- [ ] Quarterly dependency updates
- [ ] Performance optimization
- [ ] User feedback collection
- [ ] Feature usage analytics

## Rollback Plan

### Preparation
- [ ] Previous version tagged in Git
- [ ] Rollback procedure documented
- [ ] Database backup taken before deployment
- [ ] Rollback tested in staging

### If Issues Occur
1. [ ] Assess severity of issue
2. [ ] Check if hotfix possible
3. [ ] If not, initiate rollback
4. [ ] Restore previous Render deploy
5. [ ] Verify rollback successful
6. [ ] Communicate to users
7. [ ] Post-mortem analysis

## Compliance & Legal

- [ ] Privacy policy updated
- [ ] Terms of service current
- [ ] Data handling compliant with regulations (GDPR, etc.)
- [ ] User consent mechanisms in place
- [ ] Data retention policy defined
- [ ] Data deletion process implemented

## Success Criteria

Define what "success" means for your deployment:

- [ ] Uptime target: ___% (e.g., 99.9%)
- [ ] Response time target: ___s (e.g., <2s)
- [ ] Error rate target: ___% (e.g., <1%)
- [ ] User satisfaction: ___ (e.g., positive feedback)
- [ ] Cost within budget: $___/month

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Tech Lead | | | |
| DevOps | | | |
| Product Owner | | | |

---

**Last Updated**: November 2025
**Version**: 1.0.0

## Notes

Add any deployment-specific notes or exceptions here:

```
[Your notes here]
```

