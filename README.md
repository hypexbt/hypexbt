# hypexbt Twitter Bot

A Twitter bot that tweets 10-20 times per day about Hyperliquid exchange, token launches, trading signals, stats, and token fundamentals.

## Features

- Retweets and quote-tweets from @HyperliquidExch / @HyperliquidLabs
- Fresh Token Launch announcements from LiquidLaunch
- Token Graduations/Migrations from LiquidLaunch
- Auto-generated perp trading signals (15-min & 1-h momentum crosses)
- Daily Hyperliquid stats (24h volume, OI, top gainer/loser)
- Short token fundamental snapshots (circ supply, FDV, major backers)

## Content Distribution

- 15% → RT or quote-tweet @HyperliquidExch / @HyperliquidLabs news & memes
- 20% → "Fresh Token Launch" blurbs (LiquidLaunch GitBook feed & @LiquidLaunchHL timeline)
- 20% → "Token Graduations/Migrations" (LiquidLaunch events)
- 15% → Auto-generated perp trading signals (15-min & 1-h momentum crosses)
- 15% → Daily Hyperliquid stats (24h volume, OI, top gainer/loser)
- 15% → Short token fundamental snapshots (circ supply, FDV, major backers)

## Requirements

- Python 3.12
- Twitter API credentials
- Hyperliquid API access
- CoinGecko API access

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your API credentials
4. Run the bot: `python -m bot.main`

## Local Development

You can use Docker Compose for local development:

```bash
# Build and start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Deployment

### One-Click Deploy to Render.com

1. Fork this repository to your GitHub account
2. Sign up for [Render.com](https://render.com) if you haven't already
3. Click the button below to deploy to Render:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

4. Configure the following services:

#### Scheduler Service (Cron Job)

- **Name**: `hypexbt-scheduler`
- **Environment**: `Docker`
- **Dockerfile Path**: `./Dockerfile`
- **Command**: `python -m bot.main --mode scheduler`
- **Schedule**: `0 * * * *` (Runs every hour)
- **Environment Variables**: Add all variables from `.env.example`

#### WebSocket Service (Web Service)

- **Name**: `hypexbt-websocket`
- **Environment**: `Docker`
- **Dockerfile Path**: `./Dockerfile`
- **Command**: `python -m bot.main --mode websocket`
- **Environment Variables**: Add all variables from `.env.example`

### Deploy to Railway

1. Fork this repository to your GitHub account
2. Sign up for [Railway](https://railway.app) if you haven't already
3. Create a new project from GitHub repo
4. Add your repository
5. Configure the following services:

#### Scheduler Service

- **Name**: `hypexbt-scheduler`
- **Dockerfile Path**: `./Dockerfile`
- **Command Override**: `python -m bot.main --mode scheduler`
- **Environment Variables**: Add all variables from `.env.example`
- **Add a Cron Job**: Set to run every hour

#### WebSocket Service

- **Name**: `hypexbt-websocket`
- **Dockerfile Path**: `./Dockerfile`
- **Command Override**: `python -m bot.main --mode websocket`
- **Environment Variables**: Add all variables from `.env.example`

6. Deploy the services

## Environment Variables

Create a `.env` file with the following variables:

```


# Twitter API credentials
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_BEARER_TOKEN=your_bearer_token
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# API endpoints
HL_API_URL=https://api.hyperliquid.xyz
COINGECKO_API=https://api.coingecko.com/api/v3

# Slack webhook for error reporting (optional)
SLACK_WEBHOOK=your_slack_webhook_url

# Tweet scheduling configuration (optional)
MIN_TWEETS_PER_DAY=10
MAX_TWEETS_PER_DAY=20
MIN_INTERVAL_MINUTES=30
MAX_INTERVAL_MINUTES=180
ACTIVE_HOURS_START=0
ACTIVE_HOURS_END=23

# Tweet content distribution (optional)
HYPERLIQUID_NEWS_PCT=15
TOKEN_LAUNCHES_PCT=20
TOKEN_GRADUATIONS_PCT=20
TRADING_SIGNALS_PCT=15
DAILY_STATS_PCT=15
TOKEN_FUNDAMENTALS_PCT=15
```

## Testing

Run tests with pytest:

```bash
pytest
```

The test suite includes:

- Unit tests for all components
- Tests to ensure tweet text stays within 280 characters
- Tests to verify scheduler respects the tweet limits (≤ 20 tweets/day)
- Mocked Hyperliquid endpoints for testing

## Project Structure

```
hypexbt/
├── bot/
│   ├── __init__.py
│   ├── main.py                  # Main entry point
│   ├── scheduler.py             # Tweet scheduler
│   ├── twitter_client.py        # Twitter API client
│   ├── data_sources/            # Data source clients
│   │   ├── __init__.py
│   │   ├── hyperliquid_client.py
│   │   ├── liquidlaunch_client.py
│   │   └── coingecko_client.py
│   ├── tweet_generators/        # Tweet content generators
│   │   ├── __init__.py
│   │   ├── hyperliquid_news.py
│   │   ├── token_launch.py
│   │   ├── token_graduation.py
│   │   ├── trading_signal.py
│   │   ├── daily_stats.py
│   │   └── token_fundamentals.py
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       ├── config.py
│       ├── logging_setup.py
│       └── slack.py
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_twitter_client.py
│   ├── test_scheduler.py
│   └── test_tweet_generators.py
├── .env.example                 # Example environment variables
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Deployment Checklist

1. [ ] Set up Twitter Developer account and create a project
2. [ ] Generate Twitter API credentials (API key, API secret, Bearer token, Access token, Access token secret)
3. [ ] Create a Slack webhook for error notifications (optional)
4. [ ] Fork the repository to your GitHub account
5. [ ] Deploy to Render.com or Railway following the instructions above
6. [ ] Configure environment variables
7. [ ] Verify that both services (scheduler and websocket) are running
8. [ ] Monitor the logs to ensure tweets are being generated and posted
9. [ ] Set up monitoring alerts (optional)

## License

MIT
