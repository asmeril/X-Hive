import asyncio
import logging
from posting.twitter_poster import TwitterPoster, get_twitter_poster

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_twitter_poster():
    """
    Test Twitter API integration:
    1. Verify credentials
    2. Post a test tweet
    3. Get tweet data
    4. (Optional) Delete test tweet
    """
    
    print("\n" + "="*80)
    print("TWITTER POSTER TEST")
    print("="*80 + "\n")
    
    # ========================================
    # PHASE 1: INITIALIZE
    # ========================================
    
    print("🔧 PHASE 1: INITIALIZE TWITTER POSTER")
    print("-" * 80 + "\n")
    
    try:
        poster = get_twitter_poster()
        print("✅ TwitterPoster initialized\n")
    except ValueError as e:
        print(f"❌ Failed to initialize: {e}\n")
        print("Please add Twitter credentials to .env:\n")
        print("  TWITTER_API_KEY=...")
        print("  TWITTER_API_SECRET=...")
        print("  TWITTER_ACCESS_TOKEN=...")
        print("  TWITTER_ACCESS_TOKEN_SECRET=...\n")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}\n")
        return
    
    # ========================================
    # PHASE 2: VERIFY CREDENTIALS
    # ========================================
    
    print("🔐 PHASE 2: VERIFY CREDENTIALS")
    print("-" * 80 + "\n")
    
    if poster.verify_credentials():
        print("✅ Credentials verified!\n")
    else:
        print("❌ Credential verification failed\n")
        return
    
    # ========================================
    # PHASE 3: POST TEST TWEET
    # ========================================
    
    print("🐦 PHASE 3: POST TEST TWEET")
    print("-" * 80 + "\n")
    
    # Test tweet text
    test_tweet = (
        "🤖 X-Hive test tweet!\n\n"
        "Testing automated posting system. "
        "If you see this, the integration is working! 🎉\n\n"
        "#XHive #Automation #Test"
    )
    
    print(f"📝 Tweet text ({len(test_tweet)} chars):")
    print(f"\n{'-'*80}")
    print(test_tweet)
    print(f"{'-'*80}\n")
    
    # Ask for confirmation
    print("⚠️  This will post a REAL tweet to your Twitter account!")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Test cancelled\n")
        return
    
    print("\n📤 Posting tweet...\n")
    
    result = poster.post_tweet(test_tweet)
    
    if result:
        print("✅ Tweet posted successfully!\n")
        print(f"🆔 Tweet ID: {result['id']}")
        print(f"🔗 URL: {result['url']}")
        print(f"📅 Posted at: {result['posted_at']}\n")
        
        tweet_id = result['id']
        
        # ========================================
        # PHASE 4: GET TWEET DATA
        # ========================================
        
        print("📊 PHASE 4: GET TWEET DATA")
        print("-" * 80 + "\n")
        
        import time
        print("⏳ Waiting 5 seconds for Twitter to process...\n")
        time.sleep(5)
        
        tweet_data = poster.get_tweet(tweet_id)
        
        if tweet_data:
            print("✅ Tweet data retrieved:\n")
            print(f"🆔 ID: {tweet_data['id']}")
            print(f"📝 Text: {tweet_data['text'][:100]}...")
            print(f"📅 Created: {tweet_data['created_at']}")
            
            if tweet_data.get('metrics'):
                metrics = tweet_data['metrics']
                print(f"\n📊 Metrics:")
                print(f"   ❤️  Likes: {metrics.get('like_count', 0)}")
                print(f"   🔄 Retweets: {metrics.get('retweet_count', 0)}")
                print(f"   💬 Replies: {metrics.get('reply_count', 0)}")
                print(f"   👁️  Impressions: {metrics.get('impression_count', 'N/A')}")
            
            print()
        else:
            print("❌ Failed to get tweet data\n")
        
        # ========================================
        # PHASE 5: DELETE TEST TWEET (OPTIONAL)
        # ========================================
        
        print("🗑️ PHASE 5: DELETE TEST TWEET (OPTIONAL)")
        print("-" * 80 + "\n")
        
        delete = input("Delete test tweet? (yes/no): ").strip().lower()
        
        if delete == 'yes':
            print(f"\n🗑️ Deleting tweet {tweet_id}...\n")
            
            if poster.delete_tweet(tweet_id):
                print("✅ Tweet deleted successfully!\n")
            else:
                print("❌ Failed to delete tweet\n")
        else:
            print("\n✅ Test tweet kept on your timeline\n")
    
    else:
        print("❌ Failed to post tweet\n")
    
    # ========================================
    # SUMMARY
    # ========================================
    
    print("="*80)
    print("✅ TWITTER POSTER TEST COMPLETE")
    print("="*80 + "\n")
    
    print("🎉 Twitter integration is working!")
    print("   Ready for production auto-posting!\n")


if __name__ == "__main__":
    asyncio.run(test_twitter_poster())
