# hypexbt Twitter Bot Deployment Checklist

This checklist will guide you through the process of deploying the hypexbt Twitter bot to either Render.com or Railway.

## Prerequisites

- [ ] Twitter Developer Account with Elevated access
- [ ] Twitter API credentials (API key, API secret, Bearer token, Access token, Access token secret)
- [ ] GitHub account for hosting the repository
- [ ] Render.com or Railway account for deployment

## Step 1: Set Up Twitter Developer Account

1. [ ] Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. [ ] Create a new project and app
3. [ ] Apply for Elevated access if you haven't already
4. [ ] Generate API keys and tokens
5. [ ] Enable OAuth 1.0a and set up User authentication settings
6. [ ] Add callback URL if necessary

## Step 2: Prepare the Repository

1. [ ] Fork the hypexbt repository to your GitHub account
2. [ ] Clone the repository to your local machine
3. [ ] Create a `.env` file based on `.env.example` and fill in your credentials
4. [ ] Test the bot locally using `python -m bot.main --mode scheduler` and `python -m bot.main --mode websocket`
5. [ ] Push any changes back to your GitHub repository

## Step 3: Deploy to Render.com

### Scheduler Service (Cron Job)

1. [ ] Sign up for [Render.com](https://render.com) if you haven't already
2. [ ] Create a new Cron Job
3. [ ] Connect your GitHub repository
4. [ ] Configure the service:
   - **Name**: `hypexbt-scheduler`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Command**: `python -m bot.main --mode scheduler`
   - **Schedule**: `0 * * * *` (Runs every hour)
5. [ ] Add environment variables from your `.env` file
6. [ ] Deploy the service

### WebSocket Service (Web Service)

1. [ ] Create a new Web Service
2. [ ] Connect your GitHub repository
3. [ ] Configure the service:
   - **Name**: `hypexbt-websocket`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Command**: `python -m bot.main --mode websocket`
4. [ ] Add environment variables from your `.env` file
5. [ ] Deploy the service

## Step 4: Deploy to Railway

1. [ ] Sign up for [Railway](https://railway.app) if you haven't already
2. [ ] Create a new project
3. [ ] Connect your GitHub repository
4. [ ] Configure the scheduler service:
   - **Name**: `hypexbt-scheduler`
   - **Dockerfile Path**: `./Dockerfile`
   - **Command Override**: `python -m bot.main --mode scheduler`
   - Add environment variables from your `.env` file
   - Add a Cron Job to run every hour
5. [ ] Configure the WebSocket service:
   - **Name**: `hypexbt-websocket`
   - **Dockerfile Path**: `./Dockerfile`
   - **Command Override**: `python -m bot.main --mode websocket`
   - Add environment variables from your `.env` file
6. [ ] Deploy both services

## Step 5: Verify Deployment

1. [ ] Check the logs for both services to ensure they're running correctly
2. [ ] Verify that the scheduler is generating tweets at the expected frequency
3. [ ] Verify that the WebSocket service is processing trading signals
4. [ ] Check your Twitter account to ensure tweets are being posted

## Step 6: Monitoring and Maintenance

1. [ ] Set up monitoring alerts for service failures
2. [ ] Configure Slack notifications for errors (if using Slack)
3. [ ] Regularly check the logs for any issues
4. [ ] Update API credentials if they expire

## Troubleshooting

- If tweets aren't being posted, check the Twitter API credentials and rate limits
- If the scheduler isn't running, check the cron job configuration
- If the WebSocket service isn't processing signals, check the connection to the Hyperliquid API
- If you encounter any errors, check the logs for detailed information

## Additional Resources

- [Twitter API Documentation](https://developer.twitter.com/en/docs)
- [Render.com Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Hyperliquid API Documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)

