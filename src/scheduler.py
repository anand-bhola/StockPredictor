"""
Scheduler for periodic sentiment analysis and news updates.
Uses APScheduler to run tasks on a fixed interval.
"""

import logging
from typing import Callable, Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

logger = logging.getLogger(__name__)


class SentimentScheduler:
    """Manages scheduled sentiment analysis and news fetch tasks."""

    def __init__(self, config: Dict):
        """
        Initialize SentimentScheduler.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.scheduler = BackgroundScheduler(daemon=True)
        self.update_interval = config.get('news', {}).get('update_interval', 10)
        self.is_running = False

    def start(self, sentiment_update_func: Callable):
        """
        Start the scheduler with a sentiment update callback.

        Args:
            sentiment_update_func: Async function to call periodically for sentiment updates
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Add periodic task for sentiment updates
            self.scheduler.add_job(
                sentiment_update_func,
                IntervalTrigger(minutes=self.update_interval),
                id='sentiment_update',
                name='Periodic Sentiment Analysis',
                replace_existing=True,
                next_run_time=datetime.now()  # Run immediately on start
            )

            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler started with {self.update_interval}-min update interval")

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise

    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            try:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("Scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")

    def add_job(self, func: Callable, trigger: str = 'interval', **trigger_kwargs):
        """
        Add a custom job to the scheduler.

        Args:
            func: Function to execute
            trigger: Trigger type ('interval', 'cron', etc.)
            **trigger_kwargs: Arguments for the trigger
        """
        try:
            self.scheduler.add_job(func, trigger, **trigger_kwargs)
            logger.info(f"Added job: {func.__name__}")
        except Exception as e:
            logger.error(f"Error adding job: {e}")

    def get_jobs(self):
        """Get list of scheduled jobs."""
        return self.scheduler.get_jobs()

    def pause(self):
        """Pause the scheduler."""
        if self.is_running:
            self.scheduler.pause()
            logger.info("Scheduler paused")

    def resume(self):
        """Resume the scheduler."""
        if self.is_running:
            self.scheduler.resume()
            logger.info("Scheduler resumed")
