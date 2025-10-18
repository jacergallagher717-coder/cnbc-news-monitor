"""
CNBC Breaking News Monitor
Polls CNBC RSS feeds and auto-sends to Telegram bot
"""

import feedparser
import asyncio
import httpx
import os
from datetime import datetime
from hashlib import sha256

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# CNBC RSS Feeds
CNBC_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # Top News
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",   # World News
    "https://www.cnbc.com/id/15839135/device/rss/rss.html",   # Finance
]

# Track seen articles
seen_articles = set()
last_check = {}

def hash_article(title, link):
    """Create unique hash for article"""
    return sha256(f"{title}{link}".encode()).hexdigest()[:16]

def is_breaking_news(title):
    """Check if article is breaking/important news"""
    keywords = [
        'breaking', 'alert', 'fed', 'rate', 'inflation', 'jobs', 'earnings',
        'market', 'stocks', 'trump', 'biden', 'china', 'russia', 'war',
        'billion', 'million', 'nvidia', 'apple', 'tesla', 'microsoft',
        'crash', 'surge', 'plunge', 'rally', 'sell-off', 'record'
    ]
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in keywords)

async def send_to_backend(title, link):
    """Send article directly to backend for AI analysis"""
    backend_url = "https://market-impact-bot-v2.onrender.com/webhook/telegram"
    
    # Format as message text (like a user would send)
    message_text = f"{title}\n\n{link}"
    
    # Send as Telegram webhook payload
    payload = {
        "message": {
            "text": message_text,
            "chat": {"id": 123456789},  # Dummy ID
            "from": {"id": 999999999, "is_bot": False}
        }
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(backend_url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Backend error: {e}")
            return False

async def check_cnbc_feed(feed_url):
    """Check a single CNBC RSS feed for new articles"""
    try:
        feed = feedparser.parse(feed_url)
        new_articles = []
        
        for entry in feed.entries[:10]:  # Check top 10 articles
            title = entry.get('title', 'No title')
            link = entry.get('link', '')
            published = entry.get('published', '')
            
            article_hash = hash_article(title, link)
            
            # Skip if already seen
            if article_hash in seen_articles:
                continue
            
            # Check if breaking news
            if is_breaking_news(title):
                seen_articles.add(article_hash)
                new_articles.append({
                    'title': title,
                    'link': link,
                    'published': published
                })
                print(f"📰 NEW: {title}")
        
        return new_articles
        
    except Exception as e:
        print(f"❌ Error checking feed {feed_url}: {e}")
        return []

async def monitor_loop():
    """Main monitoring loop"""
    print("🚀 CNBC Monitor started!")
    print(f"📡 Monitoring {len(CNBC_FEEDS)} feeds")
    print(f"⏰ Check interval: 30 seconds")
    print(f"🔗 Backend: https://market-impact-bot-v2.onrender.com")
    print("-" * 50)
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\n🔄 Cycle #{cycle} - {now}")
            
            all_new_articles = []
            
            # Check all feeds
            for feed_url in CNBC_FEEDS:
                articles = await check_cnbc_feed(feed_url)
                all_new_articles.extend(articles)
            
            # Send to backend for analysis
            if all_new_articles:
                print(f"📨 Sending {len(all_new_articles)} articles to backend for AI analysis...")
                
                for article in all_new_articles:
                    success = await send_to_backend(article['title'], article['link'])
                    
                    if success:
                        print(f"✅ Analyzed: {article['title'][:50]}...")
                    else:
                        print(f"❌ Failed to analyze")
                    
                    await asyncio.sleep(3)  # Space out requests
            else:
                print("✅ No new articles")
            
            # Clean old hashes (keep last 1000)
            if len(seen_articles) > 1000:
                seen_articles.clear()
                print("🧹 Cleared old article cache")
            
            print(f"💾 Tracking {len(seen_articles)} articles")
            
        except Exception as e:
            print(f"❌ Error in monitor loop: {e}")
        
        # Wait before next check
        await asyncio.sleep(30)

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════╗
    ║   CNBC Breaking News Monitor v1.0     ║
    ║   Powered by Market Impact Pro        ║
    ╚═══════════════════════════════════════╝
    """)
    
    # Start monitoring
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
