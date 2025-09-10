# WolfHunt Project Configuration

## Project Context
- GMX trading bot for perpetual futures on Arbitrum
- React/TypeScript frontend (Netlify) + FastAPI backend (Railway)
- Production URL: https://wolfhunt.netlify.app/
- E2E tests in ../wolfhunt-e2e/ directory
- Price feeds use CoinGecko API with GMX fallback
- Netlify function proxying can mask Railway backend issues
- Wait 90+ seconds for Netlify deployment before testing

## Architecture Notes
- Frontend calls `/api/*` which redirects to `/.netlify/functions/api/*` 
- Netlify function proxies to Railway backend
- Backend routes are mounted without `/api` prefix in main.py
- Strategy config endpoints: GET/POST `/strategy/config`
- Wolf Configuration page replaces legacy Trading/Strategy pages

## Known Issues & Patterns
- Price feeds can break if API polling intervals conflict
- "Body stream already read" errors from polling non-existent endpoints
- toLocaleString() errors when price data is undefined
- Navigation active states must handle legacy `/trading` and `/strategy` routes