# Canvas MPC Documentation

Welcome to the Canvas MPC documentation. This directory contains all guides and references for deploying and maintaining the application.

## Quick Navigation

### 🚀 Getting Started

**New to Canvas MPC?** Start here:

1. **[QUICK_START.md](QUICK_START.md)** - Get deployed in 15 minutes
2. **[../DEPLOYMENT_README.md](../DEPLOYMENT_README.md)** - Architecture overview and deployment strategy

### 📚 Comprehensive Guides

**Need detailed information?**

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step deployment for all services
  - Supabase setup
  - Render deployment
  - Streamlit Cloud deployment
  - Configuration and testing
  - Troubleshooting

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Complete file organization guide
  - Directory structure
  - Component descriptions
  - Deployment workflow
  - Security considerations
  - Best practices

- **[FILE_STRUCTURE_DIAGRAM.md](FILE_STRUCTURE_DIAGRAM.md)** - Visual file structure
  - Deployment view
  - Directory-level view
  - Import flow
  - Data flow
  - Quick reference

## Documentation by Role

### For Developers

1. Start with [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. Review [FILE_STRUCTURE_DIAGRAM.md](FILE_STRUCTURE_DIAGRAM.md)
3. Set up local environment using [QUICK_START.md](QUICK_START.md) (development section)

### For DevOps/Deployment

1. Read [../DEPLOYMENT_README.md](../DEPLOYMENT_README.md) for architecture
2. Follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete setup
3. Use [QUICK_START.md](QUICK_START.md) for rapid deployment

### For End Users

1. Start with [QUICK_START.md](QUICK_START.md) section "Add Your Credentials"
2. Use the Settings page in the application
3. Refer to [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) "Configuration" section

## Documentation Structure

```
docs/
├── README.md                      [This file - Documentation index]
├── QUICK_START.md                 [15-minute deployment guide]
├── DEPLOYMENT_GUIDE.md            [Comprehensive deployment guide]
├── PROJECT_STRUCTURE.md           [File organization and architecture]
└── FILE_STRUCTURE_DIAGRAM.md      [Visual diagrams and references]

../
├── DEPLOYMENT_README.md           [High-level architecture overview]
├── env.example                    [Environment variables template]
├── env.backend.example            [Backend environment template]
├── env.frontend.example           [Frontend environment template]
└── render.yaml                    [Render deployment config]
```

## Common Tasks

### Initial Deployment

Follow this order:

1. **[QUICK_START.md](QUICK_START.md)** - Fastest path to deployment
   - Or -
2. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Detailed instructions

### Understanding the Architecture

1. **[../DEPLOYMENT_README.md](../DEPLOYMENT_README.md)** - System overview
2. **[FILE_STRUCTURE_DIAGRAM.md](FILE_STRUCTURE_DIAGRAM.md)** - Visual representation

### Troubleshooting

1. Check **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** → "Troubleshooting" section
2. Review **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** → "Troubleshooting" section
3. Verify configuration in respective service dashboards

### Making Changes

1. Review **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** → "Best Practices"
2. Test locally first
3. Push to GitHub (auto-deploys to Render and Streamlit)

### Adding Features

1. Review **[FILE_STRUCTURE_DIAGRAM.md](FILE_STRUCTURE_DIAGRAM.md)** → "Import Flow"
2. Understand **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** → "Component Descriptions"
3. Follow existing patterns in codebase

## Key Concepts

### Deployment Architecture

```
Frontend (Streamlit) ←→ Backend (Render) ←→ Supabase (Database)
                              ↓
                    External APIs (Canvas, Google, OpenRouter)
```

### File Organization

- **backend/**: All backend code (deploy to Render)
- **frontend/**: All frontend code (deploy to Streamlit Cloud)
- **config/**: Database schema (use in Supabase)
- **scripts/**: Local helper scripts (not deployed)
- **docs/**: Documentation (this directory)

### Per-User Credentials

Users can store their own API credentials securely in Supabase:
- Canvas API tokens
- Google OAuth tokens (Calendar, Gmail)
- Managed through Settings page
- Isolated per user with Row Level Security

## Quick Reference

| What | Where | Documentation |
|------|-------|---------------|
| 15-min setup | QUICK_START.md | Quick guide |
| Full deployment | DEPLOYMENT_GUIDE.md | Step-by-step |
| File structure | PROJECT_STRUCTURE.md | Organization |
| Architecture | ../DEPLOYMENT_README.md | Overview |
| Visual diagrams | FILE_STRUCTURE_DIAGRAM.md | Diagrams |

## Environment Variables

### Backend (Render)

See `../env.backend.example` for complete list. Required:
- `OPENROUTER_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`

### Frontend (Streamlit)

See `../env.frontend.example`. Required:
- `API_URL`

## Support

### Documentation

All documentation is in this `docs/` directory and the root `DEPLOYMENT_README.md`.

### Logs

- **Backend**: Render Dashboard → Logs
- **Frontend**: Streamlit Cloud → Logs
- **Database**: Supabase Dashboard → Logs

### Testing

Test endpoints:
- Backend health: `https://your-backend.onrender.com/health`
- Backend tools: `https://your-backend.onrender.com/tools`
- Frontend: Your Streamlit app URL

## Contributing

When adding documentation:

1. **Small updates**: Edit existing docs
2. **New features**: Update relevant sections
3. **Major changes**: Create new doc and add to this index

## Version History

- **v1.0.0** (November 2025): Initial documentation
  - Complete deployment guides
  - Architecture documentation
  - Visual diagrams
  - Quick start guide

---

**Need Help?**
- Start with [QUICK_START.md](QUICK_START.md)
- Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting section
- Review logs in service dashboards

**Last Updated**: November 2025

