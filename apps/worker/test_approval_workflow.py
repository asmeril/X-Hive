import asyncio
import logging
from datetime import datetime

# Import approval system
from approval.approval_queue import approval_queue, ApprovalQueueItem
from approval.telegram_notifier import TelegramApprovalNotifier

# Import intel system
from intel.aggregator import aggregator
from intel.ai_processor import ai_processor
from intel.base_source import ContentQuality

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_approval_workflow():
    """
    Test full approval workflow:
    1. Fetch content
    2. Process with AI
    3. Add to approval queue
    4. Send Telegram notification
    5. Wait for approval
    """
    
    print("\n" + "="*80)
    print("X-HIVE APPROVAL WORKFLOW TEST")
    print("="*80 + "\n")
    
    # ========================================
    # PHASE 1: FETCH & PROCESS CONTENT
    # ========================================
    
    print("🔍 PHASE 1: CONTENT GATHERING & AI PROCESSING")
    print("-" * 80)
    
    # Fetch content
    logger.info("Fetching content from sources...")
    items = await aggregator.fetch_all()
    
    print(f"✅ Collected {len(items)} items\n")
    
    # Get top 3 items
    top_items = aggregator.get_top_items(items, n=3)
    
    print(f"📊 Selected top 3 items for processing:\n")
    for i, item in enumerate(top_items, 1):
        print(f"{i}. {item.title[:60]}...")
        print(f"   Relevance: {item.relevance_score:.2f} | Engagement: {item.engagement_score:.2f}\n")
    
    # Process with AI
    print("🤖 Processing with AI (Gemini)...\n")
    
    processed = await ai_processor.process_batch(top_items, max_items=3)
    
    successful = [p for p in processed if p.processed]
    
    print(f"✅ Successfully processed: {len(successful)}/3\n")
    
    # Filter high quality
    high_quality = ai_processor.filter_by_quality(successful, ContentQuality.HIGH)
    
    print(f"⭐ HIGH quality tweets: {len(high_quality)}\n")
    
    if not high_quality:
        print("❌ No high-quality tweets generated. Exiting.")
        return
    
    # ========================================
    # PHASE 2: ADD TO APPROVAL QUEUE
    # ========================================
    
    print("📋 PHASE 2: APPROVAL QUEUE")
    print("-" * 80 + "\n")
    
    queue_items = []
    
    for item in high_quality:
        # Add to approval queue
        queue_item = approval_queue.add(
            content_item=item,
            generated_tweet=item.suggested_tweet
        )
        
        queue_items.append(queue_item)
        
        print(f"✅ Added to queue: {queue_item.tweet_id}")
        print(f"   Tweet: {item.suggested_tweet[:80]}...\n")
    
    print(f"📊 Total in queue: {len(approval_queue.get_pending())} pending\n")
    
    # ========================================
    # PHASE 3: TELEGRAM NOTIFICATION
    # ========================================
    
    print("📱 PHASE 3: TELEGRAM NOTIFICATION")
    print("-" * 80 + "\n")
    
    try:
        # Initialize Telegram notifier
        notifier = TelegramApprovalNotifier(approval_queue)
        
        print(f"✅ Telegram notifier initialized\n")
        
        # Send notifications
        for queue_item in queue_items:
            print(f"📤 Sending notification for: {queue_item.tweet_id}...")
            
            success = await notifier.send_approval_request(queue_item)
            
            if success:
                print(f"✅ Notification sent!\n")
            else:
                print(f"❌ Failed to send notification\n")
        
        print("━" * 80)
        print("📱 CHECK YOUR TELEGRAM!")
        print("━" * 80)
        print("\nYou should see approval requests with buttons:")
        print("  [✅ Onayla]  [❌ Reddet]  [✏️ Düzenle]  [📋 Detay]\n")
        
        print("To approve/reject tweets:")
        print("  1. Open Telegram")
        print("  2. Click buttons on messages")
        print("  3. Or use commands: /pending, /approved\n")
    
    except ValueError as e:
        print(f"⚠️  Telegram credentials not configured: {e}")
        print("\nTo enable Telegram notifications:")
        print("  1. Create bot with @BotFather")
        print("  2. Add to .env:")
        print("     TELEGRAM_BOT_TOKEN=your_token")
        print("     TELEGRAM_CHAT_ID=your_chat_id")
        print("  3. Run: pip install python-telegram-bot\n")
    
    except Exception as e:
        print(f"❌ Telegram error: {e}\n")
    
    # ========================================
    # PHASE 4: QUEUE STATUS
    # ========================================
    
    print("📊 PHASE 4: QUEUE STATUS")
    print("-" * 80 + "\n")
    
    pending = approval_queue.get_pending()
    approved = approval_queue.get_approved()
    
    print(f"📋 Pending: {len(pending)} tweets")
    print(f"✅ Approved: {len(approved)} tweets")
    print(f"📊 Total: {len(approval_queue.items)} tweets\n")
    
    if pending:
        print("📋 Pending tweets:\n")
        for item in pending[:3]:
            print(f"  • {item.tweet_id}")
            print(f"    {item.generated_tweet[:60]}...")
            print(f"    Status: {item.status.value}\n")
    
    # ========================================
    # SUMMARY
    # ========================================
    
    print("="*80)
    print("✅ APPROVAL WORKFLOW TEST COMPLETE")
    print("="*80 + "\n")
    
    print("📊 Summary:")
    print(f"   Content fetched: {len(items)} items")
    print(f"   AI processed: {len(successful)} tweets")
    print(f"   High quality: {len(high_quality)} tweets")
    print(f"   Added to queue: {len(queue_items)} tweets")
    print(f"   Telegram notifications: {'Sent' if queue_items else 'Not sent'}\n")
    
    print("🔄 Next steps:")
    print("   1. Check Telegram for approval requests")
    print("   2. Approve/reject tweets")
    print("   3. Integrate with auto-scheduler")
    print("   4. Connect to Twitter API for posting\n")


async def test_queue_only():
    """Quick test: just add mock items to queue"""
    
    print("\n" + "="*80)
    print("QUICK APPROVAL QUEUE TEST (Mock Data)")
    print("="*80 + "\n")
    
    # Create mock content item
    from intel.base_source import ContentItem, ContentCategory, ContentQuality
    
    mock_item = ContentItem(
        title="Test: Microsoft BitNet - 1-bit LLMs",
        url="https://github.com/microsoft/BitNet",
        source_type="github",
        source_name="GitHub Trending",
        category=ContentCategory.AI_ML,
        relevance_score=0.95,
        engagement_score=0.85
    )
    
    mock_item.quality = ContentQuality.HIGH
    mock_item.suggested_tweet = (
        "Microsoft'un BitNet projesi, 1-bit LLM'ler için resmi çıkarım çatısı "
        "sunarak yapay zeka dünyasında çığır açıyor. #AI #MachineLearning"
    )
    
    # Add to queue
    queue_item = approval_queue.add(
        content_item=mock_item,
        generated_tweet=mock_item.suggested_tweet
    )
    
    print(f"✅ Added mock tweet to queue: {queue_item.tweet_id}\n")
    
    # Try to send Telegram notification
    try:
        notifier = TelegramApprovalNotifier(approval_queue)
        
        print("📤 Sending Telegram notification...\n")
        
        success = await notifier.send_approval_request(queue_item)
        
        if success:
            print("✅ Notification sent to Telegram!")
            print("📱 Check your Telegram app!\n")
        else:
            print("❌ Failed to send notification\n")
    
    except ValueError as e:
        print(f"⚠️  Telegram not configured: {e}\n")
        print("Add to .env:")
        print("  TELEGRAM_BOT_TOKEN=your_token")
        print("  TELEGRAM_CHAT_ID=your_chat_id\n")
    
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Show queue status
    print(f"📊 Queue status: {len(approval_queue.get_pending())} pending\n")


if __name__ == "__main__":
    import sys
    
    # Choose test mode
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test with mock data
        asyncio.run(test_queue_only())
    else:
        # Full workflow test
        asyncio.run(test_approval_workflow())
