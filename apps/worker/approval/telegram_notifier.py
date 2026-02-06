import asyncio
import logging
from typing import Optional, List
import os
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from dotenv import load_dotenv
from pathlib import Path

from .approval_queue import ApprovalQueue, ApprovalQueueItem, ApprovalStatus

# Load .env from approval directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class TelegramApprovalNotifier:
    """
    Telegram bot for X-Hive approval notifications.
    
    Sends notifications when tweets need approval.
    Handles inline button callbacks for approve/reject/edit.
    """
    
    def __init__(
        self,
        approval_queue: ApprovalQueue,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """
        Initialize Telegram notifier.
        
        Args:
            approval_queue: ApprovalQueue instance
            bot_token: Telegram bot token (from env if not provided)
            chat_id: Chat ID to send notifications (from env if not provided)
        """
        
        self.approval_queue = approval_queue
        
        # Get credentials
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID not found")
        
        # Initialize bot
        self.bot = Bot(token=self.bot_token)
        self.application = None
        
        logger.info(f"✅ TelegramApprovalNotifier initialized (chat_id={self.chat_id})")
    
    async def send_approval_request(self, item: ApprovalQueueItem) -> bool:
        """
        Send approval request notification.
        
        Args:
            item: ApprovalQueueItem to request approval for
        
        Returns:
            Success status
        """
        
        try:
            # Format message
            message = self._format_approval_message(item)
            
            # Create inline keyboard
            keyboard = self._create_approval_keyboard(item.tweet_id)
            
            # Send message
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Sent approval request for: {item.tweet_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send approval request: {e}")
            return False
    
    def _format_approval_message(self, item: ApprovalQueueItem) -> str:
        """
        Format approval request message.
        
        Args:
            item: ApprovalQueueItem
        
        Returns:
            Formatted message text (HTML)
        """
        
        content = item.content_item
        tweet_length = len(item.generated_tweet) + len(content.url) + 1
        
        # Quality emoji
        quality_emoji = {
            'HIGH': '🌟',
            'MEDIUM': '⭐',
            'LOW': '💫'
        }
        quality = content.quality.value.upper() if content.quality else 'UNKNOWN'
        
        message = f"""🤖 <b>X-Hive Tweet Approval</b>\n\n📰 <b>Kaynak:</b> {content.source_name} ({content.source_type})\n{quality_emoji.get(quality, '⭐')} <b>Kalite:</b> {quality}\n📊 <b>Scores:</b> Relevance {content.relevance_score:.2f} | Engagement {content.engagement_score:.2f}\n\n🐦 <b>TWEET ÖNERİSİ:</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{item.generated_tweet}\n{content.url}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📏 <b>Tweet length:</b> {tweet_length}/280 karakter\n🆔 <b>ID:</b> <code>{item.tweet_id}</code>\n"""
        
        return message
    
    def _create_approval_keyboard(self, tweet_id: str) -> InlineKeyboardMarkup:
        """
        Create inline keyboard for approval.
        
        Args:
            tweet_id: Tweet ID
        
        Returns:
            InlineKeyboardMarkup
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Onayla", callback_data=f"approve:{tweet_id}"),
                InlineKeyboardButton("❌ Reddet", callback_data=f"reject:{tweet_id}")
            ],
            [
                InlineKeyboardButton("✏️ Düzenle", callback_data=f"edit:{tweet_id}"),
                InlineKeyboardButton("📋 Detay", callback_data=f"detail:{tweet_id}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle inline button callbacks.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        action, tweet_id = query.data.split(':', 1)
        
        if action == 'approve':
            await self._handle_approve(query, tweet_id)
        
        elif action == 'reject':
            await self._handle_reject(query, tweet_id)
        
        elif action == 'edit':
            await self._handle_edit(query, tweet_id)
        
        elif action == 'detail':
            await self._handle_detail(query, tweet_id)
    
    async def _handle_approve(self, query, tweet_id: str):
        """Handle approve action"""
        
        # Reload queue from disk to get latest state
        self.approval_queue._load()
        
        success = self.approval_queue.approve(tweet_id)
        
        if success:
            await query.edit_message_text(
                text=f"✅ <b>Tweet Onaylandı!</b>\n\n{query.message.text}\n\n"
                     f"🕐 Onaylandı: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Tweet approved via Telegram: {tweet_id}")
        else:
            await query.edit_message_text(
                text=f"❌ Hata: Tweet bulunamadı ({tweet_id})",
                parse_mode='HTML'
            )
    
    async def _handle_reject(self, query, tweet_id: str):
        """Handle reject action"""
        
        # Reload queue from disk to get latest state
        self.approval_queue._load()
        
        success = self.approval_queue.reject(tweet_id, reason="Rejected via Telegram")
        
        if success:
            await query.edit_message_text(
                text=f"❌ <b>Tweet Reddedildi</b>\n\n{query.message.text}\n\n"
                     f"🕐 Reddedildi: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                parse_mode='HTML'
            )
            
            logger.info(f"❌ Tweet rejected via Telegram: {tweet_id}")
        else:
            await query.edit_message_text(
                text=f"❌ Hata: Tweet bulunamadı ({tweet_id})",
                parse_mode='HTML'
            )
    
    async def _handle_edit(self, query, tweet_id: str):
        """Handle edit action"""
        
        await query.edit_message_text(
            text=f"✏️ Düzenleme özelliği yakında eklenecek!\n\n"
                 f"Şimdilik tweet'i reddet ve yenisini oluştur.\n\n"
                 f"Tweet ID: <code>{tweet_id}</code>",
            parse_mode='HTML'
        )
    
    async def _handle_detail(self, query, tweet_id: str):
        """Handle detail action"""
        
        # Reload queue from disk to get latest state
        self.approval_queue._load()
        
        item = self.approval_queue.items.get(tweet_id)
        
        if not item:
            await query.answer("❌ Tweet bulunamadı", show_alert=True)
            return
        
        detail = f"""📋 <b>Tweet Detayları</b>\n\n🆔 <b>ID:</b> <code>{item.tweet_id}</code>\n📰 <b>Başlık:</b> {item.content_item.title[:100]}...\n🔗 <b>URL:</b> {item.content_item.url}\n📅 <b>Oluşturuldu:</b> {item.created_at.strftime('%Y-%m-%d %H:%M')}\n🏷️ <b>Kategori:</b> {item.content_item.category.value if item.content_item.category else 'N/A'}\n\n📝 <b>AI Özet:</b>\n{item.content_item.ai_summary or 'N/A'}\n"""
        
        await query.answer()
        await query.message.reply_text(detail, parse_mode='HTML')
    
    async def cmd_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /pending command - Show all pending tweets
        """
        
        pending = self.approval_queue.get_pending()
        
        if not pending:
            await update.message.reply_text("📭 Bekleyen tweet yok!")
            return
        
        message = f"📋 <b>Bekleyen Tweet'ler ({len(pending)})</b>\n\n"
        
        for item in pending[:5]:  # Show max 5
            message += f"• <code>{item.tweet_id}</code>\n"
            message += f"  {item.generated_tweet[:80]}...\n\n"
        
        if len(pending) > 5:
            message += f"... ve {len(pending) - 5} tane daha"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def cmd_approved(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /approved command - Show all approved tweets
        """
        
        approved = self.approval_queue.get_approved()
        
        if not approved:
            await update.message.reply_text("📭 Onaylanmış tweet yok!")
            return
        
        message = f"✅ <b>Onaylanmış Tweet'ler ({len(approved)})</b>\n\n"
        
        for item in approved[:5]:  # Show max 5
            message += f"• <code>{item.tweet_id}</code>\n"
            message += f"  {item.generated_tweet[:80]}...\n\n"
        
        if len(approved) > 5:
            message += f"... ve {len(approved) - 5} tane daha"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    def start_bot(self):
        """
        Start Telegram bot (blocking).
        
        For use in dedicated bot process.
        """
        
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(CommandHandler("pending", self.cmd_pending))
        self.application.add_handler(CommandHandler("approved", self.cmd_approved))
        
        logger.info("🤖 Starting Telegram bot...")
        
        # Run bot
        self.application.run_polling()


# Initialize (will be used by other modules)
def create_notifier(approval_queue: ApprovalQueue) -> TelegramApprovalNotifier:
    """Create and return TelegramApprovalNotifier instance"""
    return TelegramApprovalNotifier(approval_queue)
