# Queue Worker Implementation & Testing Guide

## 🎯 **What We Built**

A generic job processing system that replaces the old tweet-specific worker. Now any job type can be processed through Redis queues with type safety, rate limiting, and retry logic.

## 🚀 **Quick Implementation**

### 1. **The System is Already Running**

When you start the app with `python src/main.py`, the new `Worker` automatically starts alongside the API server and processes jobs from Redis queues.

### 2. **How to Add Tweet Jobs**

```python
# In your scheduler or API endpoints, replace old tweet code with:
from src.queue.jobs.tweet_job import TweetJob
from src.queue.service import QueueService

# Initialize queue service
queue_service = QueueService(config.redis_url)
await queue_service.connect()

# Add a tweet job (replaces old direct Twitter posting)
job_id = await TweetJob.add_to_queue(
    queue_service,
    content="Hello from the new queue system!",
    priority=2,  # 1=urgent, 2=high, 3=normal, 4=low
    media_ids=["optional_media_id"]  # Optional
)

print(f"Tweet job {job_id} added to queue")
```

## 🧪 **Manual Testing Steps**

### Test 1: Basic Tweet Job

```python
# Add this to a test script or API endpoint
import asyncio
from src.utils.config import Config
from src.queue.service import QueueService
from src.queue.jobs.tweet_job import TweetJob

async def test_tweet_job():
    config = Config()
    queue_service = QueueService(config.redis_url)
    await queue_service.connect()

    # Add a test tweet
    job_id = await TweetJob.add_to_queue(
        queue_service,
        content="Testing the new queue worker system! 🚀",
        priority=1  # High priority
    )

    print(f"✅ Added tweet job: {job_id}")

    # Check queue stats
    stats = await queue_service.get_queue_stats()
    print(f"📊 Queue stats: {stats}")

# Run the test
asyncio.run(test_tweet_job())
```

### Test 2: Monitor Queue Processing

```python
# Check what's happening in the queues
async def monitor_queues():
    config = Config()
    queue_service = QueueService(config.redis_url)
    await queue_service.connect()

    # Get queue statistics
    stats = await queue_service.get_queue_stats()
    print("📊 Queue Stats:", stats)

    # Peek at jobs in normal priority queue
    jobs = await queue_service.peek_queue(priority=3, count=5)
    print("👀 Jobs in queue:", jobs)

    # Check retry queue
    retry_jobs = await queue_service.get_retry_jobs(count=5)
    print("🔄 Retry jobs:", retry_jobs)

    # Check dead letter queue
    dead_jobs = await queue_service.get_dead_letter_jobs(count=5)
    print("💀 Dead letter jobs:", dead_jobs)

asyncio.run(monitor_queues())
```

### Test 3: API Endpoint Integration

```python
# Add this to your FastAPI routes (src/api/server.py)
from src.queue.jobs.tweet_job import TweetJob

@app.post("/api/tweet/queue")
async def queue_tweet(content: str, priority: int = 3):
    """Add a tweet to the processing queue."""
    try:
        job_id = await TweetJob.add_to_queue(
            app.state.queue_service,  # You'll need to add this to app state
            content=content,
            priority=priority
        )
        return {"success": True, "job_id": job_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Test with curl:
# curl -X POST "http://localhost:8000/api/tweet/queue" \
#      -H "Content-Type: application/json" \
#      -d '{"content": "Hello from API!", "priority": 2}'
```

## 🔧 **Integration with Existing Code**

### Replace Old Tweet Posting

```python
# OLD WAY (direct Twitter posting):
twitter_client = TwitterClient(config)
twitter_client.post_tweet("Hello world!")

# NEW WAY (queue-based):
await TweetJob.add_to_queue(
    queue_service,
    content="Hello world!",
    priority=3
)
```

### Update Your Scheduler

```python
# In src/agent/scheduler.py or wherever you generate tweets
async def schedule_daily_stats():
    stats_content = generate_daily_stats()  # Your existing logic

    # Instead of posting directly, add to queue
    await TweetJob.add_to_queue(
        self.queue_service,  # Add this to your scheduler
        content=stats_content,
        priority=2  # High priority for daily stats
    )
```

## 📋 **Complete Test Checklist**

- [ ] **Start the app**: `python src/main.py` - Worker should start automatically
- [ ] **Add a test job**: Use the test script above
- [ ] **Check Redis**: Jobs should appear in `jobs_priority_*` queues
- [ ] **Watch logs**: Worker should process jobs and post tweets
- [ ] **Test rate limiting**: Add multiple jobs quickly, see rate limiting in action
- [ ] **Test failures**: Add invalid content, check retry queue
- [ ] **Monitor stats**: Use queue stats to see processing metrics

## 🎉 **Expected Results**

1. **Jobs get processed**: Worker pulls from Redis and posts tweets
2. **Rate limiting works**: Max tweets per day/hour respected
3. **Retries work**: Failed jobs retry with exponential backoff
4. **Type safety**: Invalid job parameters get caught by Pydantic
5. **Monitoring works**: Queue stats show job counts and processing

## 🚨 **Common Issues & Solutions**

- **Jobs not processing**: Check if Worker is running and Redis is connected
- **Rate limits hit**: Check `get_worker_stats()` for rate limiter status
- **Jobs in retry queue**: Check logs for error messages
- **Type errors**: Ensure job parameters match `TweetJobParams` schema

The system is designed to be a drop-in replacement for direct Twitter posting - just change your tweet calls to use `TweetJob.add_to_queue()` instead!
