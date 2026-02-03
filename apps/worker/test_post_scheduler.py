"""
Unit tests for PostScheduler

Tests scheduling functionality, manual posts, rescheduling, and error handling.
"""

import asyncio
import pytest
import logging
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch, call

from post_scheduler import (
    PostScheduler,
    get_scheduler,
    shutdown_scheduler,
    _scheduler_instance
)

logger = logging.getLogger(__name__)


class TestPostScheduler:
    """Test cases for PostScheduler class"""
    
    @pytest.fixture
    async def scheduler(self):
        """Create a PostScheduler instance for testing"""
        scheduler = PostScheduler()
        yield scheduler
        # Cleanup
        if scheduler.is_running:
            await scheduler.stop()
    
    def test_init_default_times(self):
        """Test initialization with default post times"""
        scheduler = PostScheduler()
        
        assert len(scheduler.post_times) == 3
        assert scheduler.post_times[0] == time(9, 0)
        assert scheduler.post_times[1] == time(14, 0)
        assert scheduler.post_times[2] == time(20, 0)
        assert not scheduler.is_running
        assert scheduler.content_generator is None
    
    def test_init_custom_times(self):
        """Test initialization with custom post times"""
        custom_times = [time(7, 30), time(12, 0), time(18, 30)]
        scheduler = PostScheduler(post_times=custom_times)
        
        assert scheduler.post_times == custom_times
    
    def test_init_custom_generator(self):
        """Test initialization with custom content generator"""
        custom_gen = lambda period: f"Custom post for {period}"
        scheduler = PostScheduler(content_generator_func=custom_gen)
        
        assert scheduler.content_generator_func == custom_gen
    
    def test_determine_time_period(self):
        """Test time period determination"""
        scheduler = PostScheduler()
        
        with patch('post_scheduler.datetime') as mock_datetime:
            # Morning: 6 AM
            mock_datetime.now.return_value.hour = 8
            assert scheduler._determine_time_period() == "morning"
            
            # Afternoon: 3 PM
            mock_datetime.now.return_value.hour = 15
            assert scheduler._determine_time_period() == "afternoon"
            
            # Evening: 10 PM
            mock_datetime.now.return_value.hour = 22
            assert scheduler._determine_time_period() == "evening"
    
    def test_default_post_generator_morning(self):
        """Test default post generator for morning"""
        scheduler = PostScheduler()
        post = scheduler._default_post_generator("morning")
        
        assert "morning" in post.lower()
        assert len(post) > 0
        assert "🌅" in post
    
    def test_default_post_generator_afternoon(self):
        """Test default post generator for afternoon"""
        scheduler = PostScheduler()
        post = scheduler._default_post_generator("afternoon")
        
        assert "afternoon" in post.lower()
        assert "☀️" in post
    
    def test_default_post_generator_evening(self):
        """Test default post generator for evening"""
        scheduler = PostScheduler()
        post = scheduler._default_post_generator("evening")
        
        assert "evening" in post.lower()
        assert "🌙" in post
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self):
        """Test starting the scheduler"""
        scheduler = PostScheduler()
        
        with patch.object(scheduler, 'content_generator') as mock_gen:
            mock_gen = AsyncMock()
            scheduler.content_generator = mock_gen
            mock_gen.start = AsyncMock()
            
            # Mock scheduler start
            scheduler.scheduler.start = MagicMock()
            
            await scheduler.start()
            
            # Verify ContentGenerator was initialized and started
            assert scheduler.is_running
            assert len(scheduler.scheduler.get_jobs()) == 3
    
    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test starting scheduler when already running"""
        scheduler = PostScheduler()
        scheduler.is_running = True
        
        # Should return early without error
        await scheduler.start()
        
        assert scheduler.is_running
    
    @pytest.mark.asyncio
    async def test_stop_scheduler(self):
        """Test stopping the scheduler"""
        scheduler = PostScheduler()
        scheduler.is_running = True
        
        mock_gen = AsyncMock()
        scheduler.content_generator = mock_gen
        mock_gen.stop = AsyncMock()
        
        # Mock scheduler
        scheduler.scheduler.shutdown = MagicMock()
        
        await scheduler.stop()
        
        assert not scheduler.is_running
        mock_gen.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_not_running(self):
        """Test stopping scheduler when not running"""
        scheduler = PostScheduler()
        scheduler.is_running = False
        
        # Should return early without error
        await scheduler.stop()
        
        assert not scheduler.is_running
    
    @pytest.mark.asyncio
    async def test_scheduled_post_job_success(self):
        """Test scheduled post job execution"""
        scheduler = PostScheduler()
        
        mock_gen = AsyncMock()
        scheduler.content_generator = mock_gen
        
        mock_result = {
            "status": "posted",
            "draft_id": "abc123",
            "task_id": "task_001",
            "risk_level": "low"
        }
        mock_gen.create_post_with_approval = AsyncMock(return_value=mock_result)
        
        result = await scheduler._scheduled_post_job()
        
        assert result["status"] == "posted"
        assert result["scheduled"] is True
        assert "timestamp" in result
        mock_gen.create_post_with_approval.assert_called_once()
        
        # Verify timeout is 1 hour (3600 seconds)
        call_args = mock_gen.create_post_with_approval.call_args
        assert call_args[1]["timeout_seconds"] == 3600
    
    @pytest.mark.asyncio
    async def test_scheduled_post_job_no_generator(self):
        """Test scheduled post job when generator not initialized"""
        scheduler = PostScheduler()
        scheduler.content_generator = None
        
        result = await scheduler._scheduled_post_job()
        
        assert result["status"] == "failed"
        assert result["scheduled"] is True
    
    @pytest.mark.asyncio
    async def test_trigger_manual_post_with_text(self):
        """Test manually triggering a post with custom text"""
        scheduler = PostScheduler()
        
        mock_gen = AsyncMock()
        scheduler.content_generator = mock_gen
        
        mock_result = {
            "status": "posted",
            "draft_id": "manual_001",
            "task_id": "task_002",
            "risk_level": "low"
        }
        mock_gen.create_post_with_approval = AsyncMock(return_value=mock_result)
        
        custom_text = "This is a manual post"
        result = await scheduler.trigger_manual_post(text=custom_text)
        
        assert result["status"] == "posted"
        assert result["manual"] is True
        
        # Verify timeout is 30 minutes (1800 seconds)
        call_args = mock_gen.create_post_with_approval.call_args
        assert call_args[1]["timeout_seconds"] == 1800
        assert call_args[0][0] == custom_text  # First positional arg is text
    
    @pytest.mark.asyncio
    async def test_trigger_manual_post_generated_text(self):
        """Test manually triggering a post with auto-generated text"""
        scheduler = PostScheduler()
        
        mock_gen = AsyncMock()
        scheduler.content_generator = mock_gen
        
        mock_result = {
            "status": "posted",
            "draft_id": "manual_002",
            "task_id": "task_003",
            "risk_level": "low"
        }
        mock_gen.create_post_with_approval = AsyncMock(return_value=mock_result)
        
        result = await scheduler.trigger_manual_post()
        
        assert result["status"] == "posted"
        assert result["manual"] is True
        
        # Verify text was generated
        call_args = mock_gen.create_post_with_approval.call_args
        assert len(call_args[0][0]) > 0  # Text should be generated
    
    @pytest.mark.asyncio
    async def test_trigger_manual_post_no_generator(self):
        """Test manual post when generator not initialized"""
        scheduler = PostScheduler()
        scheduler.content_generator = None
        
        result = await scheduler.trigger_manual_post()
        
        assert result["status"] == "failed"
        assert result["manual"] is True
    
    def test_get_next_scheduled_posts_not_running(self):
        """Test getting scheduled posts when scheduler not running"""
        scheduler = PostScheduler()
        scheduler.is_running = False
        
        posts = scheduler.get_next_scheduled_posts()
        
        assert posts == []
    
    def test_get_next_scheduled_posts_running(self):
        """Test getting scheduled posts when scheduler is running"""
        scheduler = PostScheduler()
        scheduler.is_running = True
        
        mock_job = MagicMock()
        mock_job.id = "scheduled_post_09_00"
        mock_job.name = "Post at 09:00"
        mock_job.next_run_time = datetime.now()
        mock_job.trigger = MagicMock()
        mock_job.trigger.timezone = "UTC"
        
        scheduler.scheduler.get_jobs = MagicMock(return_value=[mock_job])
        scheduler.scheduler.running = True
        
        posts = scheduler.get_next_scheduled_posts()
        
        assert len(posts) == 1
        assert posts[0]["job_id"] == "scheduled_post_09_00"
        assert posts[0]["time"] == "Post at 09:00"
    
    def test_reschedule_not_running(self):
        """Test rescheduling when scheduler not running"""
        scheduler = PostScheduler()
        scheduler.is_running = False
        
        result = scheduler.reschedule([time(10, 0), time(15, 0)])
        
        assert result is False
    
    def test_reschedule_success(self):
        """Test successful rescheduling"""
        scheduler = PostScheduler()
        scheduler.is_running = True
        scheduler.scheduler.running = True
        
        scheduler.scheduler.remove_all_jobs = MagicMock()
        scheduler.scheduler.add_job = MagicMock()
        
        new_times = [time(10, 0), time(15, 0), time(19, 0)]
        result = scheduler.reschedule(new_times)
        
        assert result is True
        assert scheduler.post_times == new_times
        scheduler.scheduler.remove_all_jobs.assert_called_once()
        assert scheduler.scheduler.add_job.call_count == 3
    
    @pytest.mark.asyncio
    async def test_singleton_get_scheduler_new(self):
        """Test creating new singleton instance"""
        # Reset singleton
        import post_scheduler
        post_scheduler._scheduler_instance = None
        
        scheduler = await get_scheduler()
        
        assert scheduler is not None
        assert isinstance(scheduler, PostScheduler)
    
    @pytest.mark.asyncio
    async def test_singleton_get_scheduler_existing(self):
        """Test getting existing singleton instance"""
        # Reset and create first instance
        import post_scheduler
        post_scheduler._scheduler_instance = None
        
        scheduler1 = await get_scheduler()
        scheduler2 = await get_scheduler()
        
        assert scheduler1 is scheduler2
    
    @pytest.mark.asyncio
    async def test_shutdown_scheduler(self):
        """Test shutting down singleton scheduler"""
        # Reset and create instance
        import post_scheduler
        post_scheduler._scheduler_instance = None
        
        scheduler = await get_scheduler()
        assert scheduler is not None
        
        await shutdown_scheduler()
        
        assert post_scheduler._scheduler_instance is None


class TestPostSchedulerIntegration:
    """Integration tests for PostScheduler with mocked ContentGenerator"""
    
    @pytest.mark.asyncio
    async def test_full_scheduled_workflow(self):
        """Test complete scheduled posting workflow"""
        post_times = [time(10, 0)]  # Single test time
        scheduler = PostScheduler(post_times=post_times)
        
        # Mock ContentGenerator
        with patch('post_scheduler.ContentGenerator') as mock_gen_class:
            mock_gen = AsyncMock()
            mock_gen_class.return_value = mock_gen
            mock_gen.start = AsyncMock()
            mock_gen.stop = AsyncMock()
            mock_gen.create_post_with_approval = AsyncMock(
                return_value={
                    "status": "posted",
                    "draft_id": "test_001",
                    "task_id": "task_001",
                    "risk_level": "low"
                }
            )
            
            scheduler.scheduler.start = MagicMock()
            
            await scheduler.start()
            
            assert scheduler.is_running
            assert len(scheduler.scheduler.get_jobs()) == 1
            
            await scheduler.stop()
            
            assert not scheduler.is_running


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
