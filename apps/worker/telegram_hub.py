"""
X-Hive Telegram Hub — Tam Entegrasyon Merkezi

4 Rol:
1. 📲 BİLDİRİM — Thread hazır, yayınlandı, sniper reply bildirimleri
2. 📱 MOBİL ONAY — Telefondan thread onayla/reddet/yayınla
3. 📢 KANAL YAYINI — Onaylanan thread'leri Telegram kanalına otomatik at (X linki ile)
4. 📥 İNTEL KAYNAĞI — Telegram kanallarından haber toplama (orchestrator'a bağlanır)

Tek bir bot, tek bir token, tüm roller.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from interaction_tracker import get_interaction_tracker
from sniper_guard import build_focus_keywords, is_relevant_for_sniper
from config import settings

load_dotenv()

try:
    from telegram import (
        Update, InlineKeyboardButton, InlineKeyboardMarkup,
        Bot, InputMediaPhoto
    )
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        ContextTypes, MessageHandler, filters
    )
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)

# ─── CONFIG ────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # Admin DM / özel grup
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")  # Yayın kanalı (@xhive_feed vb.)
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "")  # Tartışma grubu (opsiyonel)


class TelegramHub:
    """
    X-Hive Telegram Hub — Tüm Telegram operasyonlarını yöneten merkez.
    
    Singleton pattern ile çalışır.
    """
    
    _instance: Optional["TelegramHub"] = None
    
    def __new__(cls) -> "TelegramHub":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.admin_chat_id = TELEGRAM_ADMIN_CHAT_ID
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.group_id = TELEGRAM_GROUP_ID
        
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self._running = False
        
        # Pending approval futures (tweet_id -> asyncio.Future)
        self.pending_approvals: Dict[str, asyncio.Future] = {}
        
        self._initialized = True
        
        if not TELEGRAM_AVAILABLE:
            logger.warning("⚠️ python-telegram-bot not installed. pip install python-telegram-bot")
        
        logger.info("✅ TelegramHub initialized")
    
    # ═══════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════
    
    async def start(self) -> bool:
        """Bot'u başlat ve polling'i aç"""
        if not TELEGRAM_AVAILABLE:
            logger.warning("⚠️ Telegram devre dışı (kütüphane yok)")
            return False
        
        if not self.bot_token:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN boş, Telegram devre dışı")
            return False
        
        if self._running:
            logger.debug("Telegram Hub zaten çalışıyor")
            return True
        
        try:
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot
            
            # ── Komutlar ──
            self.application.add_handler(CommandHandler("start", self._cmd_start))
            self.application.add_handler(CommandHandler("status", self._cmd_status))
            self.application.add_handler(CommandHandler("scan", self._cmd_scan))
            self.application.add_handler(CommandHandler("pending", self._cmd_pending))
            self.application.add_handler(CommandHandler("analytics", self._cmd_analytics))
            self.application.add_handler(CommandHandler("help", self._cmd_help))
            
            # ── Buton callback'leri ──
            self.application.add_handler(CallbackQueryHandler(self._handle_callback))
            
            # Start polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            self._running = True
            logger.info("🤖 TelegramHub started (polling active)")
            
            # Admin'e başlangıç bildirimi
            await self._safe_send(
                self.admin_chat_id,
                "🚀 *X\\-Hive Telegram Hub başlatıldı\\!*\n\n"
                "Kullanılabilir komutlar:\n"
                "/pending — Bekleyen thread'leri gör\n"
                "/scan — Yeni tarama başlat\n"
                "/analytics — Sonuç dashboard'u\n"
                "/status — Sistem durumu\n"
                "/help — Yardım",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ TelegramHub start failed: {e}")
            return False
    
    async def stop(self):
        """Bot'u durdur"""
        if not self._running:
            return
        
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            self._running = False
            logger.info("🛑 TelegramHub stopped")
        except Exception as e:
            logger.error(f"❌ TelegramHub stop error: {e}")
    
    # ═══════════════════════════════════════════════════════
    # 1. BİLDİRİMLER (Notifications)
    # ═══════════════════════════════════════════════════════
    
    async def notify_threads_ready(self, count: int, top_score: float = 0):
        """Yeni thread'ler hazır olduğunda admin'e bildir"""
        text = (
            f"🧵 *{count} yeni viral thread hazır\\!*\n\n"
            f"🏆 En yüksek skor: *{top_score}/10*\n"
            f"📱 /pending ile incele ve onayla\n"
            f"🖥️ Veya Desktop UI'dan kontrol et"
        )
        await self._safe_send(self.admin_chat_id, text, parse_mode=ParseMode.MARKDOWN_V2)
    
    async def notify_thread_posted(self, title: str, tweet_count: int, tweet_url: str = ""):
        """Thread X'e yayınlandığında bildir"""
        url_text = f"\n🔗 [Tweeti gör]({tweet_url})" if tweet_url else ""
        text = (
            f"✅ *Thread yayınlandı\\!*\n\n"
            f"📝 {self._escape_md(title[:80])}\n"
            f"🧵 {tweet_count} tweet{url_text}"
        )
        await self._safe_send(self.admin_chat_id, text, parse_mode=ParseMode.MARKDOWN_V2)
    
    async def notify_sniper_sent(self, target: str, reply_preview: str = ""):
        """Sniper reply gönderildiğinde bildir"""
        text = (
            f"🎯 *Sniper Reply gönderildi\\!*\n\n"
            f"Hedef: @{self._escape_md(target)}\n"
            f"💬 _{self._escape_md(reply_preview[:100])}_"
        )
        await self._safe_send(self.admin_chat_id, text, parse_mode=ParseMode.MARKDOWN_V2)
    
    async def notify_error(self, error_msg: str):
        """Kritik hata bildirimi"""
        text = f"🚨 *X\\-Hive Hata\\!*\n\n`{self._escape_md(error_msg[:300])}`"
        await self._safe_send(self.admin_chat_id, text, parse_mode=ParseMode.MARKDOWN_V2)
    
    async def notify_daily_summary(self, stats: Dict[str, Any]):
        """Günlük özet raporu"""
        text = (
            f"📊 *Günlük X\\-Hive Raporu*\n\n"
            f"🧵 Üretilen thread: *{stats.get('threads_generated', 0)}*\n"
            f"✅ Yayınlanan: *{stats.get('threads_posted', 0)}*\n"
            f"🎯 Sniper reply: *{stats.get('sniper_replies', 0)}*\n"
            f"👀 Toplam impression: *{stats.get('total_impressions', 'N/A')}*\n"
            f"🔥 En viral: *{stats.get('top_viral_score', 0)}/10*"
        )
        await self._safe_send(self.admin_chat_id, text, parse_mode=ParseMode.MARKDOWN_V2)
    
    # ═══════════════════════════════════════════════════════
    # 2. MOBİL ONAY (Mobile Approval via Telegram)
    # ═══════════════════════════════════════════════════════
    
    async def send_thread_for_approval(self, tweet_id: str, title: str,
                                         viral_score: float, tr_thread: List[str],
                                         en_thread: List[str], mentions: List[str] = None,
                                         image_url: str = None, source: str = ""):
        """
        Thread'i Telegram'a gönder, butonlarla onay/red/yayınla seçenekleri sun.
        """
        # Thread önizleme (ilk 2 tweet)
        preview_tweets = tr_thread[:2] if tr_thread else en_thread[:2]
        preview = "\n\n".join([f"📝 _{self._escape_md(t[:150])}_" for t in preview_tweets])
        
        # Mention bilgisi
        mention_text = ""
        if mentions:
            mention_text = f"\n🏷️ Etiketler: {' '.join(mentions)}"
        
        # Görsel bilgisi
        image_text = "\n🖼️ Görsel: ✅ Hazır" if image_url else ""
        
        score_emoji = "🔥" if viral_score >= 8 else "🚀" if viral_score >= 6 else "📈"
        
        text = (
            f"{score_emoji} *Viral Skor: {viral_score}/10*\n"
            f"📰 Kaynak: {self._escape_md(source)}\n"
            f"📌 {self._escape_md(title[:100])}\n"
            f"{mention_text}{image_text}\n\n"
            f"🧵 *TR Thread Önizleme:*\n{preview}\n"
            f"\\.\\.\\. \\({len(tr_thread)} tweet\\)\n\n"
            f"🇬🇧 EN Thread: {len(en_thread)} tweet"
        )
        
        # Butonlar
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚀 Yayınla (TR)", callback_data=f"post_tr:{tweet_id}"),
                InlineKeyboardButton("🚀 Yayınla (EN)", callback_data=f"post_en:{tweet_id}"),
            ],
            [
                InlineKeyboardButton("✅ Onayla", callback_data=f"approve:{tweet_id}"),
                InlineKeyboardButton("❌ Reddet", callback_data=f"reject:{tweet_id}"),
            ],
            [
                InlineKeyboardButton("🎯 Sniper Reply", callback_data=f"sniper:{tweet_id}"),
            ]
        ])
        
        # Görsel varsa foto ile gönder
        if image_url and image_url.startswith("http"):
            try:
                await self.bot.send_photo(
                    chat_id=self.admin_chat_id,
                    photo=image_url,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return
            except Exception:
                pass  # Fallback to text
        
        await self._safe_send(self.admin_chat_id, text, reply_markup=keyboard,
                              parse_mode=ParseMode.MARKDOWN_V2)
    
    # ═══════════════════════════════════════════════════════
    # 3. KANAL YAYINI (Channel Broadcasting)
    # ═══════════════════════════════════════════════════════
    
    async def broadcast_thread_to_channel(self, title: str, tr_thread: List[str],
                                            x_tweet_url: str = "",
                                            image_url: str = None,
                                            viral_score: float = 0):
        """
        Onaylanan thread'i Telegram kanalına yayınla.
        İnsanlar Telegram'da görür → X'e trafik akar.
        
        Format:
        - Görsel (varsa)
        - Thread özeti (ilk 2-3 tweet)
        - "Devamını X'te oku 👉 [link]"
        """
        if not self.channel_id:
            logger.debug("📢 Telegram channel ID not configured, skipping broadcast")
            return False
        
        try:
            # Thread özetini oluştur
            preview = "\n\n".join(tr_thread[:3])  # İlk 3 tweet
            escaped_title = self._escape_md(title)
            escaped_preview = self._escape_md(preview)
            escaped_cta = self._escape_md(cta) if cta else ""
            
            # CTA
            cta = ""
            if x_tweet_url:
                cta = f"\n\n🔗 Devamını X'te oku 👉 {x_tweet_url}"
            
            score_bar = "🔥" * min(int(viral_score), 10) if viral_score else ""
            
            channel_text = (
                f"🧵 {escaped_title}\n"
                f"{score_bar}\n\n"
                f"{escaped_preview}"
                f"{escaped_cta}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📲 @xhive\\_feed \\| AI & Tech Threads"
            )
            
            # Görsel varsa foto ile gönder
            if image_url and image_url.startswith("http"):
                try:
                    await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=image_url,
                        caption=channel_text,
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    logger.info(f"📢 Thread broadcast to channel (with image): {title[:50]}")
                    return True
                except Exception as img_err:
                    logger.warning(f"⚠️ Photo send failed, falling back to text: {img_err}")
            
            # Metin olarak gönder
            await self._safe_send(self.channel_id, channel_text,
                                  parse_mode=ParseMode.MARKDOWN_V2)
            logger.info(f"📢 Thread broadcast to channel: {title[:50]}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Channel broadcast failed: {e}")
            return False
    
    async def broadcast_daily_digest(self, threads: List[Dict[str, Any]]):
        """
        Günlük digest: Bugün yayınlanan tüm thread'leri tek bir mesajda özetle.
        """
        if not self.channel_id or not threads:
            return
        
        lines = ["📊 *Bugünün En Viral Thread'leri*\n"]
        for i, t in enumerate(threads[:5], 1):
            score = t.get("viral_score", 0)
            title = self._escape_md(t.get("title", "Thread")[:60])
            url = t.get("x_url", "")
            link = f"[Oku]({url})" if url else ""
            lines.append(f"{i}\\. {self._score_emoji(score)} *{score}/10* \\- {title} {link}")
        
        lines.append(f"\n📲 @xhive\\_feed")
        
        text = "\n".join(lines)
        await self._safe_send(self.channel_id, text, parse_mode=ParseMode.MARKDOWN_V2)
    
    # ═══════════════════════════════════════════════════════
    # KOMUTLAR (Bot Commands)
    # ═══════════════════════════════════════════════════════
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start"""
        await update.message.reply_text(
            "🐝 *X\\-Hive Telegram Hub*\n\n"
            "AI destekli viral içerik yönetim sisteminize hoş geldiniz\\!\n\n"
            "*Komutlar:*\n"
            "📋 /pending — Bekleyen thread'leri gör ve onayla\n"
            "🔍 /scan — Yeni içerik taraması başlat\n"
            "📈 /analytics — Sonuç dashboard'u\n"
            "📊 /status — Sistem durumu\n"
            "❓ /help — Detaylı yardım\n\n"
            "_Thread'ler hazır olduğunda burada bildirim alacaksınız\\!_",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        await update.message.reply_text(
            "📖 *X\\-Hive Kullanım Rehberi*\n\n"
            "*🧵 Thread İş Akışı:*\n"
            "1\\. /scan ile yeni içerik taraması başlatın\n"
            "2\\. AI en viral 8 içeriği seçer ve TR\\+EN thread üretir\n"
            "3\\. /pending ile thread'leri telefonunuzdan inceleyin\n"
            "4\\. 🚀 butonuyla doğrudan X'e yayınlayın\n"
            "5\\. 🎯 ile büyük hesaplara sniper reply gönderin\n\n"
            "*📢 Kanal Yayını:*\n"
            "Yayınlanan thread'ler otomatik olarak Telegram kanalınıza da atılır\\.\n"
            "Takipçiler Telegram'dan görür → X'e tıklar → impression artar\\!\n\n"
            "*📲 Bildirimler:*\n"
            "• Thread hazır ✅\n"
            "• Thread yayınlandı 🚀\n"
            "• Sniper reply gönderildi 🎯\n"
            "• Hata oluştu 🚨",
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _cmd_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analytics — Sonuç dashboard özetini gönder"""
        try:
            from approval.approval_queue import approval_queue
            tracker = get_interaction_tracker()
            dashboard = tracker.build_dashboard(approval_queue=approval_queue, limit=12)

            kpis = dashboard.get("kpis", {})
            queue = dashboard.get("queue", {})
            viral_proxy = dashboard.get("viral_proxy", {})

            text = (
                "📈 *X\\-Hive Analytics*\n\n"
                f"🧵 Thread başarı \(24s\): *{kpis.get('thread_success_24h', 0)}* "
                f"/ ❌ *{kpis.get('thread_failed_24h', 0)}*\n"
                f"🎯 Sniper başarı \(24s\): *{kpis.get('sniper_success_24h', 0)}* "
                f"/ ❌ *{kpis.get('sniper_failed_24h', 0)}*\n"
                f"✅ Onay \(24s\): *{kpis.get('approvals_24h', 0)}* | "
                f"⛔ Red: *{kpis.get('rejections_24h', 0)}*\n\n"
                f"📦 Queue: Toplam *{queue.get('total', 0)}* | "
                f"Bekleyen *{queue.get('pending', 0)}* | "
                f"İşlenen *{queue.get('processed', 0)}*\n"
                f"🔥 Avg Processed Score: *{viral_proxy.get('avg_processed_score', 0)}*"
            )
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            await update.message.reply_text(f"❌ Analytics alınamadı: {e}")
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status — Sistem durumunu göster"""
        try:
            from orchestrator import orchestrator as orch
            status = orch.get_status()
            running = "✅ Çalışıyor" if status.get("running") else "❌ Durdu"
            
            from approval.approval_queue import approval_queue
            pending = len(approval_queue.get_pending())
            approved = len(approval_queue.get_approved())
            
            text = (
                f"📊 *X\\-Hive Sistem Durumu*\n\n"
                f"🤖 Orkestratör: {running}\n"
                f"📋 Bekleyen thread: *{pending}*\n"
                f"✅ Onaylanan: *{approved}*\n"
                f"📢 Kanal: {'✅ Aktif' if self.channel_id else '❌ Yapılandırılmamış'}\n"
                f"🕐 Zaman: {datetime.now().strftime('%H:%M:%S')}"
            )
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            await update.message.reply_text(f"❌ Durum alınamadı: {e}")
    
    async def _cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan — Manuel tarama başlat"""
        try:
            await update.message.reply_text("🔍 Yeni tarama başlatılıyor... (2-5 dk sürebilir)")
            
            from orchestrator import orchestrator as orch
            if not orch._running:
                await update.message.reply_text("❌ Orkestratör çalışmıyor!")
                return
            
            # Background'da taramayı başlat
            asyncio.create_task(self._run_scan_and_notify(update.effective_chat.id))
            
        except Exception as e:
            await update.message.reply_text(f"❌ Tarama başlatılamadı: {e}")
    
    async def _run_scan_and_notify(self, chat_id: int):
        """Taramayı çalıştır ve tamamlanınca bildir"""
        try:
            from orchestrator import orchestrator as orch
            result = await orch.run_intel_collection_once()
            
            items_count = result.get("items_collected", 0)
            
            from approval.approval_queue import approval_queue
            pending = approval_queue.get_pending()
            
            if pending:
                top_score = max(p.viral_score for p in pending)
                text = (
                    f"✅ *Tarama tamamlandı\\!*\n\n"
                    f"📦 Toplanan: {items_count} içerik\n"
                    f"🧵 Üretilen thread: *{len(pending)}*\n"
                    f"🏆 En yüksek skor: *{top_score}/10*\n\n"
                    f"/pending ile inceleyin"
                )
            else:
                text = f"✅ Tarama tamamlandı\\. {items_count} içerik toplandı ama yeni thread üretilemedi\\."
            
            await self._safe_send(chat_id, text, parse_mode=ParseMode.MARKDOWN_V2)
            
        except Exception as e:
            await self._safe_send(chat_id, f"❌ Tarama hatası: {e}")
    
    async def _cmd_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pending — Bekleyen thread'leri listele ve onay butonlarıyla gönder"""
        try:
            from approval.approval_queue import approval_queue
            pending = approval_queue.get_pending()
            pending.sort(key=lambda x: x.viral_score, reverse=True)
            
            if not pending:
                await update.message.reply_text("📭 Bekleyen thread yok. /scan ile yeni tarama yapın.")
                return
            
            await update.message.reply_text(
                f"📋 *{len(pending)} bekleyen thread:*\n_En yüksek skorlular önce_",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            # Her thread'i butonlarla gönder (max 8)
            for item in pending[:8]:
                await self.send_thread_for_approval(
                    tweet_id=item.tweet_id,
                    title=item.content_item.title,
                    viral_score=item.viral_score,
                    tr_thread=item.tr_thread,
                    en_thread=item.en_thread,
                    mentions=item.mentions if hasattr(item, 'mentions') else [],
                    image_url=item.image_url if hasattr(item, 'image_url') else None,
                    source=item.content_item.source_name,
                )
                await asyncio.sleep(0.5)  # Rate limit
                
        except Exception as e:
            await update.message.reply_text(f"❌ Hata: {e}")
    
    # ═══════════════════════════════════════════════════════
    # CALLBACK HANDLER (Buton tıklamaları)
    # ═══════════════════════════════════════════════════════
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tüm inline buton callback'lerini yönet"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if ":" not in data:
            return
        
        action, tweet_id = data.split(":", 1)
        
        try:
            from approval.approval_queue import approval_queue, ApprovalStatus
            tracker = get_interaction_tracker()
            
            if tweet_id not in approval_queue.items:
                await query.edit_message_text("⚠️ Bu thread artık mevcut değil veya işlendi.")
                return
            
            item = approval_queue.items[tweet_id]
            
            if action == "approve":
                approval_queue.approve(tweet_id)
                await query.edit_message_text(
                    f"✅ *Onaylandı:* {self._escape_md(item.content_item.title[:60])}\n\n"
                    f"Desktop UI'dan veya /pending'den yayınlayabilirsiniz\\.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            
            elif action == "reject":
                approval_queue.reject(tweet_id)
                await query.edit_message_text(
                    f"❌ *Reddedildi:* {self._escape_md(item.content_item.title[:60])}",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            
            elif action in ("post_tr", "post_en"):
                lang = "tr" if action == "post_tr" else "en"
                thread = item.tr_thread if lang == "tr" else item.en_thread
                
                if not thread:
                    await query.edit_message_text(f"⚠️ {lang.upper()} thread boş!")
                    return

                tracker.record_event(
                    action="thread_publish",
                    status="started",
                    item_id=tweet_id,
                    source="telegram",
                    details={"language": lang, "tweet_count": len(thread)},
                    viral_score=float(getattr(item, "viral_score", 0) or 0),
                )
                
                await query.edit_message_text(
                    f"🚀 *{lang.upper()} Thread yayınlanıyor\\.\\.\\.* \\({len(thread)} tweet\\)",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                # Background'da X'e yayınla
                asyncio.create_task(
                    self._post_thread_and_notify(
                        tweet_id=tweet_id,
                        thread=thread,
                        title=item.content_item.title,
                        image_url=getattr(item, 'image_url', None),
                        mentions=getattr(item, 'mentions', []),
                        chat_id=update.effective_chat.id
                    )
                )
            
            elif action == "sniper":
                sniper_targets = getattr(item, 'sniper_targets', [])
                if not sniper_targets:
                    tracker.record_event(
                        action="sniper",
                        status="no_targets",
                        item_id=tweet_id,
                        source="telegram",
                        details={},
                        viral_score=float(getattr(item, "viral_score", 0) or 0),
                    )
                    await query.edit_message_text("⚠️ Bu içerik için sniper hedefi bulunamadı.")
                    return
                
                targets = [t.get("handle", t.get("username", "?")) for t in sniper_targets[:3]]
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Sniper Onayla", callback_data=f"sniper_confirm:{tweet_id}"),
                        InlineKeyboardButton("❌ İptal", callback_data=f"sniper_cancel:{tweet_id}"),
                    ]
                ])

                await query.edit_message_text(
                    f"🎯 *Sniper Reply hazır*\n"
                    f"Hedefler: {', '.join(self._escape_md(t) for t in targets)}\n\n"
                    f"Gerçek reply gönderimi için onaylayın\.",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN_V2
                )

            elif action == "sniper_confirm":
                sniper_targets = getattr(item, 'sniper_targets', [])
                tracker.record_event(
                    action="sniper",
                    status="started",
                    item_id=tweet_id,
                    source="telegram",
                    details={"target_count": len(sniper_targets[:3])},
                    viral_score=float(getattr(item, "viral_score", 0) or 0),
                )

                await query.edit_message_text(
                    "✅ *Sniper onaylandı*\. Gerçek reply gönderimi başlatılıyor\.\.\.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )

                asyncio.create_task(
                    self._run_sniper_and_notify(tweet_id, update.effective_chat.id)
                )

            elif action == "sniper_cancel":
                tracker.record_event(
                    action="sniper",
                    status="cancelled",
                    item_id=tweet_id,
                    source="telegram",
                    details={},
                    viral_score=float(getattr(item, "viral_score", 0) or 0),
                )
                await query.edit_message_text("🛑 Sniper işlemi iptal edildi.")
            
            else:
                logger.warning(f"Unknown callback action: {action}")
                
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
            try:
                await query.edit_message_text(f"❌ İşlem hatası: {e}")
            except:
                pass
    
    # ═══════════════════════════════════════════════════════
    # BACKGROUND TASKS
    # ═══════════════════════════════════════════════════════
    
    async def _post_thread_and_notify(self, tweet_id: str, thread: List[str],
                                        title: str, image_url: str = None,
                                        mentions: List[str] = None,
                                        chat_id: int = None):
        """Thread'i X'e yayınla, sonra Telegram'a ve kanala bildir"""
        try:
            from x_daemon import XDaemon
            from approval.approval_queue import approval_queue, ApprovalStatus
            tracker = get_interaction_tracker()
            
            x_daemon = XDaemon()
            previous_url = None
            first_tweet_url = None
            failed_step = 0
            
            # Mention'ları ilk tweet'e ekle
            if mentions:
                mention_text = " ".join(mentions[:2])
                thread[0] = f"{thread[0]}\n\n{mention_text}"
            
            for i, tweet_text in enumerate(thread):
                try:
                    if i == 0:
                        images = [image_url] if image_url else None
                        result = await x_daemon.post_tweet(text=tweet_text, images=images)
                        if result.get("success") and result.get("tweet_url"):
                            previous_url = result["tweet_url"]
                            first_tweet_url = result["tweet_url"]
                    else:
                        if previous_url:
                            result = await x_daemon.reply_to_tweet(
                                tweet_url=previous_url, text=tweet_text
                            )
                            if result.get("success") and result.get("tweet_url"):
                                previous_url = result["tweet_url"]
                    
                    logger.info(f"🐦 Thread tweet {i+1}/{len(thread)} posted")
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"❌ Thread tweet {i+1} failed: {e}")
                    failed_step = i + 1
                    tracker.record_event(
                        action="thread_publish",
                        status="failed",
                        item_id=tweet_id,
                        source="telegram",
                        details={"failed_step": i + 1, "error": str(e)},
                    )
                    break
            
            # Status güncelle
            if tweet_id in approval_queue.items and failed_step == 0:
                item = approval_queue.items[tweet_id]
                approval_queue.items[tweet_id].status = ApprovalStatus.PROCESSED
                approval_queue._save()
                tracker.record_event(
                    action="thread_publish",
                    status="success",
                    item_id=tweet_id,
                    source="telegram",
                    details={"tweet_count": len(thread), "tweet_url": first_tweet_url or ""},
                    viral_score=float(getattr(item, "viral_score", 0) or 0),
                )
            
            # Admin'e bildir
            notify_chat = chat_id or self.admin_chat_id
            await self._safe_send(
                notify_chat,
                f"✅ *Thread yayınlandı\\!* 🎉\n\n"
                f"📝 {self._escape_md(title[:60])}\n"
                f"🧵 {len(thread)} tweet\n"
                f"{'🔗 ' + first_tweet_url if first_tweet_url else ''}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            # Kanala da yayınla
            await self.broadcast_thread_to_channel(
                title=title,
                tr_thread=thread,
                x_tweet_url=first_tweet_url or "",
                image_url=image_url,
            )
            
        except Exception as e:
            logger.error(f"❌ Post & notify failed: {e}")
            get_interaction_tracker().record_event(
                action="thread_publish",
                status="failed",
                item_id=tweet_id,
                source="telegram",
                details={"error": str(e)},
            )
            if chat_id:
                await self._safe_send(chat_id, f"❌ Thread yayınlanamadı: {e}")
    
    async def _run_sniper_and_notify(self, tweet_id: str, chat_id: int):
        """Sniper reply'ları çalıştır ve bildir"""
        try:
            from approval.approval_queue import approval_queue
            from ai_content_generator import get_ai_generator
            from x_daemon import XDaemon
            tracker = get_interaction_tracker()
            
            item = approval_queue.items.get(tweet_id)
            if not item:
                return
            
            ai = get_ai_generator()
            x_daemon = XDaemon()
            targets = getattr(item, 'sniper_targets', [])[:3]
            sent = 0
            skipped_unrelated = 0
            skipped_missing_url = 0
            focus_keywords = build_focus_keywords(
                title=item.content_item.title,
                body=item.generated_tweet[:300],
            )
            
            for target in targets:
                username = target.get("username", "")
                name = target.get("name", "")
                
                try:
                    reply_prompt = f"""
@{username} ({name}) hesabına, aşağıdaki konuyla ilgili DEĞER KATAN kısa bir reply yaz.

Konu: {item.content_item.title}
Detay: {item.generated_tweet[:200]}

Kurallar:
- Max 200 karakter
- Yeni bilgi veya farklı bakış açısı ekle
- Doğal ol, spam görünme
- 1 emoji max
- Link KOYMA
- Sadece reply metnini döndür
"""
                    reply_text = await ai._generate_with_retry(reply_prompt, max_retries=2)

                    target_tweet_url = target.get("tweet_url") or target.get("url")
                    if not target_tweet_url and settings.SNIPER_ALLOW_FALLBACK:
                        latest_context = await x_daemon.get_latest_tweet_context(username)
                        if latest_context.get("success"):
                            target_tweet_url = latest_context.get("tweet_url", "")
                            latest_text = latest_context.get("tweet_text", "")
                            relevant, score, _ = is_relevant_for_sniper(latest_text, focus_keywords, minimum_hits=2)
                            if not relevant:
                                skipped_unrelated += 1
                                logger.info(f"⏭️ Sniper skip @{username}: unrelated latest tweet (score={score})")
                                continue

                    if not target_tweet_url or "/status/" not in target_tweet_url:
                        skipped_missing_url += 1
                        logger.warning(f"⚠️ Sniper tweet URL bulunamadı: @{username}")
                        continue

                    result = await x_daemon.reply_to_tweet(
                        tweet_url=target_tweet_url,
                        text=reply_text,
                    )
                    if not result.get("success"):
                        logger.warning(f"⚠️ Sniper reply failed for @{username}: {result.get('error')}")
                        continue

                    logger.info(f"🎯 Sniper reply sent for @{username}: {reply_text[:80]}...")
                    await self.notify_sniper_sent(username, reply_text)
                    sent += 1
                    
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"❌ Sniper to @{username} failed: {e}")
            
            await self._safe_send(
                chat_id,
                f"🎯 *Sniper Reply tamamlandı:* {sent}/{len(targets)} gönderildi"
                f"\n⏭️ İlgisiz olduğu için atlanan: {skipped_unrelated}"
                f"\n🔒 URL yok/fallback kapalı olduğu için atlanan: {skipped_missing_url}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            tracker.record_event(
                action="sniper",
                status="success",
                item_id=tweet_id,
                source="telegram",
                details={
                    "sent_count": sent,
                    "target_count": len(targets),
                    "skipped_unrelated": skipped_unrelated,
                    "skipped_missing_url": skipped_missing_url,
                    "fallback_enabled": bool(settings.SNIPER_ALLOW_FALLBACK),
                },
                viral_score=float(getattr(item, "viral_score", 0) or 0),
            )
            
        except Exception as e:
            logger.error(f"❌ Sniper & notify failed: {e}")
            get_interaction_tracker().record_event(
                action="sniper",
                status="failed",
                item_id=tweet_id,
                source="telegram",
                details={"error": str(e)},
            )
            await self._safe_send(chat_id, f"❌ Sniper reply hatası: {e}")
    
    # ═══════════════════════════════════════════════════════
    # YARDIMCI FONKSIYONLAR
    # ═══════════════════════════════════════════════════════
    
    async def _safe_send(self, chat_id, text: str, **kwargs):
        """Güvenli mesaj gönder (hata yutma)"""
        if not self.bot or not chat_id:
            logger.debug(f"Cannot send telegram: bot={bool(self.bot)}, chat_id={chat_id}")
            return
        
        try:
            await self.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        except Exception as e:
            logger.error(f"❌ Telegram send failed to {chat_id}: {e}")
            # MarkdownV2 escape hatası olabilir, plain text dene
            try:
                plain = text.replace("*", "").replace("_", "").replace("\\", "")
                await self.bot.send_message(chat_id=chat_id, text=plain)
            except Exception as e2:
                logger.error(f"❌ Telegram fallback send also failed: {e2}")
    
    @staticmethod
    def _escape_md(text: str) -> str:
        """MarkdownV2 için özel karakterleri escape et"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#',
                         '+', '-', '=', '|', '{', '}', '.', '!']
        for ch in special_chars:
            text = text.replace(ch, f'\\{ch}')
        return text
    
    @staticmethod
    def _score_emoji(score: float) -> str:
        if score >= 9: return "🔥"
        if score >= 7: return "🚀"
        if score >= 5: return "📈"
        return "📉"


# ═══════════════════════════════════════════════════════
# Singleton Access
# ═══════════════════════════════════════════════════════

_hub_instance: Optional[TelegramHub] = None


def get_telegram_hub() -> TelegramHub:
    """Get singleton TelegramHub instance"""
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = TelegramHub()
    return _hub_instance


async def start_telegram_hub() -> bool:
    """Start TelegramHub (call from lifespan)"""
    hub = get_telegram_hub()
    return await hub.start()


async def stop_telegram_hub():
    """Stop TelegramHub (call from lifespan)"""
    hub = get_telegram_hub()
    await hub.stop()
