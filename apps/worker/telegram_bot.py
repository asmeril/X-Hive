"""
Telegram Bot for X-Hive approval workflow.
Sends draft posts for human approval with SEND/EDIT/SKIP options.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import json

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
except ImportError:
    raise ImportError("Install python-telegram-bot: pip install python-telegram-bot")

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


class ApprovalStatus:
    """Approval decision status"""
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TelegramApprovalBot:
    """
    Telegram bot for human-in-the-loop approval workflow.
    
    Features:
    - Send draft posts for approval
    - Inline keyboard with SEND/EDIT/SKIP buttons
    - Callback handling for decisions
    - Timeout mechanism (default 1 hour)
    """
    
    _instance: Optional["TelegramApprovalBot"] = None
    
    def __new__(cls) -> "TelegramApprovalBot":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Telegram bot"""
        if hasattr(self, "_initialized"):
            return
        
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.application: Optional[Application] = None
        self._running = False
        
        # Store pending approvals {message_id: {data, callback}}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        
        self._initialized = True
        logger.info("✅ TelegramApprovalBot initialized")
    
    async def start(self) -> None:
        """Start the Telegram bot"""
        if self._running:
            logger.warning("⚠️ Bot already running")
            return
        
        try:
            # Create application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self._cmd_start))
            self.application.add_handler(CommandHandler("status", self._cmd_status))
            self.application.add_handler(CallbackQueryHandler(self._handle_callback))
            
            # Start polling in background
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self._running = True
            logger.info("🤖 Telegram bot started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Telegram bot"""
        if not self._running:
            return
        
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            self._running = False
            logger.info("🛑 Telegram bot stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {e}")
    
    async def request_approval(
        self,
        draft_id: str,
        text: str,
        risk_level: str = "medium",
        timeout_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Send draft post for approval and wait for decision.
        
        Args:
            draft_id: Unique draft identifier
            text: Draft post text
            risk_level: Risk assessment (low/medium/high)
            timeout_seconds: Approval timeout (default 1 hour)
        
        Returns:
            {
                "status": "approved" | "edited" | "skipped" | "timeout",
                "text": str,  # Original or edited text
                "timestamp": str
            }
        """
        
        # Risk emoji
        risk_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴"
        }.get(risk_level, "⚪")
        
        # Format message
        message = (
            f"📝 **New Draft Post**\n"
            f"{risk_emoji} Risk Level: {risk_level.upper()}\n"
            f"🆔 Draft ID: `{draft_id}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{text}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏰ Expires: {timeout_seconds // 60} minutes"
        )
        
        # Inline keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ SEND", callback_data=f"approve:{draft_id}"),
                InlineKeyboardButton("✏️ EDIT", callback_data=f"edit:{draft_id}"),
                InlineKeyboardButton("⏭️ SKIP", callback_data=f"skip:{draft_id}")
            ]
        ])
        
        # Send message
        try:
            sent_message = await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            # Store pending approval
            approval_future = asyncio.Future()
            self.pending_approvals[draft_id] = {
                "message_id": sent_message.message_id,
                "text": text,
                "risk_level": risk_level,
                "future": approval_future,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"📤 Approval request sent: {draft_id}")
            
            # Wait for decision with timeout
            try:
                result = await asyncio.wait_for(approval_future, timeout=timeout_seconds)
                return result
            
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Approval timeout: {draft_id}")
                self.pending_approvals.pop(draft_id, None)
                return {
                    "status": ApprovalStatus.TIMEOUT,
                    "text": text,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"❌ Failed to send approval request: {e}")
            raise
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        action, draft_id = query.data.split(":", 1)
        
        if draft_id not in self.pending_approvals:
            await query.edit_message_text("⚠️ This draft has expired or already been processed.")
            return
        
        approval_data = self.pending_approvals[draft_id]
        
        # Handle action
        if action == "approve":
            result = {
                "status": ApprovalStatus.APPROVED,
                "text": approval_data["text"],
                "timestamp": datetime.now().isoformat()
            }
            await query.edit_message_text(
                f"✅ **APPROVED**\n\n{approval_data['text']}\n\n🚀 Posting now..."
            )
        
        elif action == "skip":
            result = {
                "status": ApprovalStatus.SKIPPED,
                "text": approval_data["text"],
                "timestamp": datetime.now().isoformat()
            }
            await query.edit_message_text(
                f"⏭️ **SKIPPED**\n\n{approval_data['text']}\n\n🗑️ Draft discarded."
            )
        
        elif action == "edit":
            # For now, just return EDITED status (manual edit in next version)
            result = {
                "status": ApprovalStatus.EDITED,
                "text": approval_data["text"],  # TODO: Add text edit functionality
                "timestamp": datetime.now().isoformat()
            }
            await query.edit_message_text(
                f"✏️ **EDIT REQUESTED**\n\n⚠️ Manual edit feature coming soon.\n"
                f"For now, use SKIP and create new draft."
            )
        
        else:
            logger.warning(f"Unknown action: {action}")
            return
        
        # Resolve future
        if not approval_data["future"].done():
            approval_data["future"].set_result(result)
        
        # Remove from pending
        self.pending_approvals.pop(draft_id, None)
        
        logger.info(f"✅ Approval processed: {draft_id} -> {result['status']}")
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 **X-Hive Approval Bot**\n\n"
            "I'll send you draft posts for approval.\n"
            "Use the buttons to SEND, EDIT, or SKIP each post.\n\n"
            "Commands:\n"
            "/status - Show pending approvals"
        )
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        if not self.pending_approvals:
            await update.message.reply_text("✅ No pending approvals")
            return
        
        status_text = f"📋 **Pending Approvals: {len(self.pending_approvals)}**\n\n"
        for draft_id, data in self.pending_approvals.items():
            status_text += f"• `{draft_id}` ({data['risk_level']})\n"
        
        await update.message.reply_text(status_text, parse_mode="Markdown")


# Singleton access
async def get_telegram_bot() -> TelegramApprovalBot:
    """Get or create Telegram bot instance"""
    bot = TelegramApprovalBot()
    if not bot._running:
        await bot.start()
    return bot


async def shutdown_telegram_bot() -> None:
    """Shutdown Telegram bot"""
    bot = TelegramApprovalBot()
    await bot.stop()