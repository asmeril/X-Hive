import asyncio
import logging
from datetime import datetime, timedelta

# Import scheduler
from scheduling.post_scheduler import PostScheduler, get_scheduler, PostStatus
from approval.approval_queue import approval_queue

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_scheduler():
    """
    Test post scheduling system:
    1. Get approved tweets from queue
    2. Auto-schedule them
    3. Show schedule
    4. Test daily quota
    5. Test conflict resolution
    """
    
    print("\n" + "="*80)
    print("X-HIVE POST SCHEDULER TEST")
    print("="*80 + "\n")
    
    # ========================================
    # PHASE 1: INITIALIZE SCHEDULER
    # ========================================
    
    print("🔧 PHASE 1: INITIALIZE SCHEDULER")
    print("-" * 80)
    
    scheduler = get_scheduler(approval_queue)
    
    print(f"✅ Scheduler initialized")
    print(f"⏰ Time slots: {', '.join([t.strftime('%H:%M') for t in scheduler.time_slots])}")
    print(f"📊 Max daily posts: {scheduler.max_daily_posts}")
    print(f"📅 Existing scheduled posts: {len(scheduler.scheduled_posts)}\n")
    
    # ========================================
    # PHASE 2: CHECK APPROVED TWEETS
    # ========================================
    
    print("📋 PHASE 2: CHECK APPROVED TWEETS")
    print("-" * 80 + "\n")
    
    approved = approval_queue.get_approved()
    
    print(f"✅ Approved tweets: {len(approved)}\n")
    
    if approved:
        for i, item in enumerate(approved[:5], 1):
            print(f"{i}. {item.tweet_id}")
            print(f"   {item.generated_tweet[:60]}...")
            print(f"   Approved: {item.approved_at.strftime('%Y-%m-%d %H:%M') if item.approved_at else 'N/A'}\n")
    else:
        print("⚠️  No approved tweets found!")
        print("   Please approve some tweets first using Telegram bot.\n")
        print("   Run: /pending in Telegram, then click ✅ Onayla\n")
        return
    
    # ========================================
    # PHASE 3: AUTO-SCHEDULE
    # ========================================
    
    print("📅 PHASE 3: AUTO-SCHEDULE APPROVED TWEETS")
    print("-" * 80 + "\n")
    
    newly_scheduled = scheduler.schedule_approved_tweets()
    
    if newly_scheduled:
        print(f"✅ Scheduled {len(newly_scheduled)} new tweets:\n")
        
        for post in newly_scheduled:
            print(f"📌 {post.post_id}")
            print(f"   Tweet: {post.approval_item.generated_tweet[:50]}...")
            print(f"   Scheduled for: {post.scheduled_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Status: {post.status.value}\n")
    else:
        print("ℹ️  No new tweets to schedule (all already scheduled)\n")
    
    # ========================================
    # PHASE 4: SHOW FULL SCHEDULE
    # ========================================
    
    print("📅 PHASE 4: FULL POSTING SCHEDULE")
    print("=" * 80 + "\n")
    
    upcoming = scheduler.get_upcoming_posts(limit=20)
    
    if upcoming:
        print(f"📊 Upcoming posts ({len(upcoming)}):\n")
        
        current_date = None
        
        for i, post in enumerate(upcoming, 1):
            post_date = post.scheduled_time.date()
            
            # Print date header if new day
            if post_date != current_date:
                current_date = post_date
                print(f"\n📅 {post_date.strftime('%A, %Y-%m-%d')}")
                print("-" * 80)
            
            print(f"\n{i}. ⏰ {post.scheduled_time.strftime('%H:%M')}")
            print(f"   🆔 {post.post_id}")
            print(f"   🐦 {post.approval_item.generated_tweet[:70]}...")
            print(f"   📊 Quality: {post.approval_item.content_item.quality.value if post.approval_item.content_item.quality else 'N/A'}")
            print(f"   🔗 {post.approval_item.content_item.url}")
        
        print("\n" + "=" * 80)
    else:
        print("📭 No upcoming posts scheduled\n")
    
    # ========================================
    # PHASE 5: CHECK POSTS DUE NOW
    # ========================================
    
    print("\n⏰ PHASE 5: POSTS DUE NOW")
    print("-" * 80 + "\n")
    
    due_posts = scheduler.get_posts_due_now(tolerance_minutes=60)  # Within 1 hour
    
    if due_posts:
        print(f"🔥 {len(due_posts)} post(s) due for posting:\n")
        
        for post in due_posts:
            print(f"📌 {post.post_id}")
            print(f"   Scheduled: {post.scheduled_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Tweet: {post.approval_item.generated_tweet[:60]}...")
            print(f"   Status: {post.status.value}\n")
    else:
        print("ℹ️  No posts due right now\n")
    
    # ========================================
    # PHASE 6: SCHEDULE STATISTICS
    # ========================================
    
    print("📊 PHASE 6: SCHEDULE STATISTICS")
    print("-" * 80 + "\n")
    
    # Count posts by status
    scheduled_count = sum(
        1 for p in scheduler.scheduled_posts.values()
        if p.status == PostStatus.SCHEDULED
    )
    posted_count = sum(
        1 for p in scheduler.scheduled_posts.values()
        if p.status == PostStatus.POSTED
    )
    failed_count = sum(
        1 for p in scheduler.scheduled_posts.values()
        if p.status == PostStatus.FAILED
    )
    
    # Count posts by day
    posts_by_day = {}
    for post in scheduler.scheduled_posts.values():
        if post.status != PostStatus.SCHEDULED:
            continue
        
        day = post.scheduled_time.date()
        posts_by_day[day] = posts_by_day.get(day, 0) + 1
    
    print(f"📊 Overall Statistics:")
    print(f"   Total posts: {len(scheduler.scheduled_posts)}")
    print(f"   ⏰ Scheduled: {scheduled_count}")
    print(f"   ✅ Posted: {posted_count}")
    print(f"   ❌ Failed: {failed_count}\n")
    
    if posts_by_day:
        print(f"📅 Posts per day:")
        for day in sorted(posts_by_day.keys())[:7]:
            count = posts_by_day[day]
            day_name = day.strftime('%A, %Y-%m-%d')
            
            # Show quota usage
            quota_bar = "█" * count + "░" * (scheduler.max_daily_posts - count)
            
            print(f"   {day_name}: {quota_bar} ({count}/{scheduler.max_daily_posts})")
        print()
    
    # ========================================
    # PHASE 7: NEXT AVAILABLE SLOT
    # ========================================
    
    print("🔮 PHASE 7: NEXT AVAILABLE SLOT")
    print("-" * 80 + "\n")
    
    next_slot = scheduler._find_next_slot()
    
    if next_slot:
        now = datetime.now()
        time_until = next_slot - now
        hours_until = time_until.total_seconds() / 3600
        
        print(f"✅ Next available slot:")
        print(f"   📅 {next_slot.strftime('%A, %Y-%m-%d')}")
        print(f"   ⏰ {next_slot.strftime('%H:%M')}")
        print(f"   ⏳ In {hours_until:.1f} hours\n")
    else:
        print("⚠️  No available slots in next 7 days (all full!)\n")
    
    # ========================================
    # SUMMARY
    # ========================================
    
    print("="*80)
    print("✅ POST SCHEDULER TEST COMPLETE")
    print("="*80 + "\n")
    
    print("📊 Summary:")
    print(f"   Approved tweets: {len(approved)}")
    print(f"   Newly scheduled: {len(newly_scheduled)}")
    print(f"   Total scheduled: {scheduled_count}")
    print(f"   Posts due now: {len(due_posts)}")
    print(f"   Next slot: {next_slot.strftime('%Y-%m-%d %H:%M') if next_slot else 'None'}\n")
    
    print("🔄 Next steps:")
    print("   1. Review schedule above")
    print("   2. Implement Twitter API posting")
    print("   3. Create background worker to auto-post")
    print("   4. Set up monitoring and alerts\n")


if __name__ == "__main__":
    asyncio.run(test_scheduler())
