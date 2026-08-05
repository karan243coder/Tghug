"""
Advanced Telegram AI Image Editor Bot
- Full Progress Display System
- Flood Wait Protection
- Proper Button Handling
- Crash-Proof Architecture
"""

import os
import io
import sys
import time
import asyncio
import logging
import traceback
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import (
    TelegramError,
    BadRequest,
    TimedOut,
    NetworkError,
    Forbidden,
    RetryAfter,
)

import httpx

# Load environment
load_dotenv()

# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("ImageEditorBot")


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class Config:
    """Bot configuration"""
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    HF_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "")
    
    # API endpoints
    HF_BASE_URL: str = "https://api-inference.huggingface.co/models"
    HF_MODEL: str = "stabilityai/stable-diffusion-xl-base-1.0"
    
    # Timing
    FLOOD_WAIT_MAX_RETRIES: int = 5
    FLOOD_WAIT_BASE_DELAY: float = 1.0
    API_TIMEOUT: int = 180
    PROGRESS_UPDATE_INTERVAL: float = 3.0
    
    # Image processing
    MAX_IMAGE_SIZE: tuple = (1024, 1024)
    IMG2IMG_STRENGTH: float = 0.45
    GUIDANCE_SCALE: float = 7.5
    INFERENCE_STEPS: int = 30


config = Config()


# ============================================================
# PROCESS STAGES
# ============================================================

class ProcessStage(Enum):
    """All possible processing stages"""
    IDLE = auto()
    RECEIVED_IMAGE = auto()
    VALIDATING_IMAGE = auto()
    WAITING_PROMPT = auto()
    PROCESSING_PROMPT = auto()
    PREPARING_API_REQUEST = auto()
    UPLOADING_IMAGE = auto()
    AI_PROCESSING = auto()
    DOWNLOADING_RESULT = auto()
    POST_PROCESSING = auto()
    SENDING_RESULT = auto()
    COMPLETE = auto()
    ERROR = auto()


# ============================================================
# PROGRESS TRACKER
# ============================================================

@dataclass
class ProgressTracker:
    """Advanced progress tracking system"""
    stage: ProcessStage = ProcessStage.IDLE
    start_time: float = field(default_factory=time.time)
    stage_start_time: float = field(default_factory=time.time)
    progress_percent: int = 0
    current_step: int = 0
    total_steps: int = 9
    error_message: Optional[str] = None
    api_call_count: int = 0
    retry_count: int = 0
    
    # Stage descriptions
    STAGE_INFO: Dict[ProcessStage, Dict[str, Any]] = field(default_factory=lambda: {
        ProcessStage.IDLE: {
            "emoji": "⚪",
            "title": "Idle",
            "desc": "Waiting for input",
            "percent": 0,
            "step": 0,
        },
        ProcessStage.RECEIVED_IMAGE: {
            "emoji": "📸",
            "title": "Image Received",
            "desc": "Photo successfully received",
            "percent": 10,
            "step": 1,
        },
        ProcessStage.VALIDATING_IMAGE: {
            "emoji": "🔍",
            "title": "Validating Image",
            "desc": "Checking image format and size",
            "percent": 15,
            "step": 2,
        },
        ProcessStage.WAITING_PROMPT: {
            "emoji": "✍️",
            "title": "Waiting for Prompt",
            "desc": "Please enter your editing prompt",
            "percent": 20,
            "step": 3,
        },
        ProcessStage.PROCESSING_PROMPT: {
            "emoji": "📝",
            "title": "Processing Prompt",
            "desc": "Enhancing prompt for best results",
            "percent": 30,
            "step": 4,
        },
        ProcessStage.PREPARING_API_REQUEST: {
            "emoji": "📦",
            "title": "Preparing Request",
            "desc": "Setting up API parameters",
            "percent": 40,
            "step": 5,
        },
        ProcessStage.UPLOADING_IMAGE: {
            "emoji": "☁️",
            "title": "Uploading Image",
            "desc": "Sending image to AI server",
            "percent": 50,
            "step": 6,
        },
        ProcessStage.AI_PROCESSING: {
            "emoji": "🤖",
            "title": "AI Processing",
            "desc": "AI is editing your image (this takes time)",
            "percent": 65,
            "step": 7,
        },
        ProcessStage.DOWNLOADING_RESULT: {
            "emoji": "⬇️",
            "title": "Downloading Result",
            "desc": "Getting edited image from server",
            "percent": 80,
            "step": 8,
        },
        ProcessStage.POST_PROCESSING: {
            "emoji": "🎨",
            "title": "Post Processing",
            "desc": "Optimizing image quality",
            "percent": 90,
            "step": 9,
        },
        ProcessStage.SENDING_RESULT: {
            "emoji": "📤",
            "title": "Sending Result",
            "desc": "Delivering your edited image",
            "percent": 95,
            "step": 9,
        },
        ProcessStage.COMPLETE: {
            "emoji": "✅",
            "title": "Complete!",
            "desc": "Image editing finished successfully",
            "percent": 100,
            "step": 9,
        },
        ProcessStage.ERROR: {
            "emoji": "❌",
            "title": "Error",
            "desc": "Something went wrong",
            "percent": 0,
            "step": 0,
        },
    })
    
    def set_stage(self, stage: ProcessStage, error_msg: Optional[str] = None):
        """Update current stage"""
        self.stage = stage
        self.stage_start_time = time.time()
        info = self.STAGE_INFO.get(stage, {})
        self.progress_percent = info.get("percent", self.progress_percent)
        self.current_step = info.get("step", self.current_step)
        if error_msg:
            self.error_message = error_msg
    
    def get_elapsed_time(self) -> str:
        """Get formatted elapsed time"""
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.0f}s"
        elif elapsed < 3600:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def get_stage_elapsed(self) -> str:
        """Get current stage elapsed time"""
        elapsed = time.time() - self.stage_start_time
        return f"{elapsed:.0f}s"
    
    def get_progress_bar(self, length: int = 15) -> str:
        """Generate visual progress bar"""
        filled = int(length * self.progress_percent / 100)
        empty = length - filled
        
        if self.progress_percent < 30:
            color = "🟥"
        elif self.progress_percent < 60:
            color = "🟨"
        elif self.progress_percent < 90:
            color = "🟦"
        else:
            color = "🟩"
        
        bar = color * filled + "⬜" * empty
        return bar
    
    def get_stage_list(self) -> str:
        """Get visual stage checklist"""
        stages_order = [
            ProcessStage.RECEIVED_IMAGE,
            ProcessStage.VALIDATING_IMAGE,
            ProcessStage.WAITING_PROMPT,
            ProcessStage.PROCESSING_PROMPT,
            ProcessStage.PREPARING_API_REQUEST,
            ProcessStage.UPLOADING_IMAGE,
            ProcessStage.AI_PROCESSING,
            ProcessStage.DOWNLOADING_RESULT,
            ProcessStage.POST_PROCESSING,
        ]
        
        lines = []
        current_reached = False
        
        for i, stage in enumerate(stages_order, 1):
            info = self.STAGE_INFO.get(stage, {})
            emoji = info.get("emoji", "⚪")
            title = info.get("title", "")
            
            if stage == self.stage:
                current_reached = True
                lines.append(f"➡️ {emoji} {title} ← CURRENT")
            elif not current_reached:
                lines.append(f"✅ {emoji} {title}")
            else:
                lines.append(f"⬜ {emoji} {title}")
        
        return "\n".join(lines)
    
    def get_full_display(self, prompt: Optional[str] = None) -> str:
        """Generate complete progress display"""
        info = self.STAGE_INFO.get(self.stage, {})
        
        # Header
        display = "╔══════════════════════════════════════╗\n"
        display += "║    🤖 AI IMAGE EDITOR - PROGRESS    ║\n"
        display += "╚══════════════════════════════════════╝\n\n"
        
        # Status
        status_emoji = info.get("emoji", "⚪")
        status_title = info.get("title", "Unknown")
        status_desc = info.get("desc", "")
        
        display += f"📊 **STATUS:** {status_emoji} {status_title}\n"
        display += f"📋 **DETAIL:** {status_desc}\n\n"
        
        # Progress bar
        display += f"⏳ **PROGRESS:** {self.progress_percent}%\n"
        display += f"{self.get_progress_bar()}\n"
        display += f"📍 **STEP:** {self.current_step}/{self.total_steps}\n\n"
        
        # Time info
        display += f"⏱️ **TOTAL TIME:** {self.get_elapsed_time()}\n"
        display += f"⏱️ **STAGE TIME:** {self.get_stage_elapsed()}\n\n"
        
        # Prompt if available
        if prompt:
            display += f"✏️ **YOUR PROMPT:**\n_{prompt}_\n\n"
        
        # API stats
        if self.api_call_count > 0:
            display += f"🔄 **API CALLS:** {self.api_call_count}\n"
        if self.retry_count > 0:
            display += f"🔁 **RETRIES:** {self.retry_count}\n"
        
        # Stage checklist
        display += "\n📝 **PROCESS CHECKLIST:**\n"
        display += "```\n"
        display += self.get_stage_list()
        display += "\n```\n"
        
        # Error info
        if self.stage == ProcessStage.ERROR and self.error_message:
            display += f"\n❌ **ERROR:** {self.error_message}\n"
        
        return display
    
    def get_compact_display(self, prompt: Optional[str] = None) -> str:
        """Get compact version for quick updates"""
        info = self.STAGE_INFO.get(self.stage, {})
        emoji = info.get("emoji", "⚪")
        title = info.get("title", "Unknown")
        
        display = f"{emoji} **{title}** | {self.progress_percent}% | {self.get_elapsed_time()}\n"
        display += f"{self.get_progress_bar(10)}\n"
        
        if prompt:
            display += f"✏️ Prompt: _{prompt[:50]}{'...' if len(prompt) > 50 else ''}_"
        
        return display


# ============================================================
# USER STATE MANAGER
# ============================================================

@dataclass
class UserState:
    """User state container"""
    user_id: int
    state: str = "idle"
    image_bytes: Optional[bytes] = None
    file_id: Optional[str] = None
    prompt: Optional[str] = None
    prompt_type: Optional[str] = None
    progress: ProgressTracker = field(default_factory=ProgressTracker)
    last_message_id: Optional[int] = None
    last_progress_message_id: Optional[int] = None
    created_at: float = field(default_factory=time.time)
    
    def reset(self):
        """Reset state to idle"""
        self.state = "idle"
        self.image_bytes = None
        self.file_id = None
        self.prompt = None
        self.prompt_type = None
        self.progress = ProgressTracker()
        self.last_progress_message_id = None


class UserManager:
    """Thread-safe user state manager"""
    
    def __init__(self):
        self._users: Dict[int, UserState] = {}
        self._lock = asyncio.Lock()
    
    async def get_or_create(self, user_id: int) -> UserState:
        """Get existing or create new user state"""
        async with self._lock:
            if user_id not in self._users:
                self._users[user_id] = UserState(user_id=user_id)
            return self._users[user_id]
    
    async def get(self, user_id: int) -> Optional[UserState]:
        """Get user state"""
        async with self._lock:
            return self._users.get(user_id)
    
    async def reset(self, user_id: int):
        """Reset user state"""
        async with self._lock:
            if user_id in self._users:
                self._users[user_id].reset()
    
    async def cleanup_old(self, max_age: int = 3600):
        """Cleanup states older than max_age seconds"""
        async with self._lock:
            current_time = time.time()
            to_remove = [
                uid for uid, state in self._users.items()
                if current_time - state.created_at > max_age
            ]
            for uid in to_remove:
                del self._users[uid]
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old user states")


user_manager = UserManager()


# ============================================================
# FLOOD WAIT PROTECTION
# ============================================================

class FloodWaitProtection:
    """Handles Telegram API rate limiting and flood protection"""
    
    def __init__(self):
        self._last_call_time: Dict[str, float] = {}
        self._min_interval: float = 0.1  # Minimum time between calls
        self._flood_wait_until: Dict[int, float] = {}  # chat_id -> wait until timestamp
    
    async def wait_if_needed(self, chat_id: int, action: str = "message"):
        """Wait if we're in a flood wait period"""
        current_time = time.time()
        
        # Check if we're in flood wait for this chat
        if chat_id in self._flood_wait_until:
            wait_until = self._flood_wait_until[chat_id]
            if current_time < wait_until:
                wait_time = wait_until - current_time
                logger.warning(f"Flood wait: sleeping {wait_time:.1f}s for chat {chat_id}")
                await asyncio.sleep(wait_time)
        
        # Ensure minimum interval between calls
        last_call = self._last_call_time.get(action, 0)
        elapsed = current_time - last_call
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        self._last_call_time[action] = time.time()
    
    def handle_retry_after(self, chat_id: int, retry_after: int):
        """Handle RetryAfter exception"""
        wait_until = time.time() + retry_after + 1  # +1 for safety
        self._flood_wait_until[chat_id] = wait_until
        logger.warning(f"Flood wait: must wait {retry_after}s for chat {chat_id}")
    
    def clear_flood_wait(self, chat_id: int):
        """Clear flood wait for a chat"""
        self._flood_wait_until.pop(chat_id, None)


flood_protection = FloodWaitProtection()


# ============================================================
# SAFE TELEGRAM API WRAPPER
# ============================================================

class SafeTelegramAPI:
    """Wrapper for Telegram API with flood wait protection and error handling"""
    
    def __init__(self, application: Application):
        self.app = application
        self.bot = application.bot
    
    async def safe_send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        reply_to_message_id: Optional[int] = None,
        disable_web_page_preview: bool = True,
    ) -> Optional[Message]:
        """Send message with flood wait protection"""
        for attempt in range(config.FLOOD_WAIT_MAX_RETRIES):
            try:
                await flood_protection.wait_if_needed(chat_id, "message")
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    reply_to_message_id=reply_to_message_id,
                    disable_web_page_preview=disable_web_page_preview,
                )
                flood_protection.clear_flood_wait(chat_id)
                return message
                
            except RetryAfter as e:
                logger.warning(f"RetryAfter: {e.retry_after}s for chat {chat_id}")
                flood_protection.handle_retry_after(chat_id, e.retry_after)
                await asyncio.sleep(e.retry_after + 1)
                continue
                
            except TimedOut:
                logger.warning(f"Timeout sending message to {chat_id}, attempt {attempt + 1}")
                await asyncio.sleep(2 ** attempt)
                continue
                
            except Forbidden:
                logger.error(f"Bot blocked by user {chat_id}")
                return None
                
            except BadRequest as e:
                logger.error(f"Bad request: {e}")
                # Try without parse_mode
                try:
                    return await self.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        reply_to_message_id=reply_to_message_id,
                        disable_web_page_preview=disable_web_page_preview,
                    )
                except:
                    return None
                    
            except TelegramError as e:
                logger.error(f"Telegram error: {e}")
                if attempt < config.FLOOD_WAIT_MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    async def safe_edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Optional[Message]:
        """Edit message with flood wait protection"""
        for attempt in range(config.FLOOD_WAIT_MAX_RETRIES):
            try:
                await flood_protection.wait_if_needed(chat_id, "edit")
                message = await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
                flood_protection.clear_flood_wait(chat_id)
                return message
                
            except RetryAfter as e:
                logger.warning(f"RetryAfter: {e.retry_after}s for edit in chat {chat_id}")
                flood_protection.handle_retry_after(chat_id, e.retry_after)
                await asyncio.sleep(e.retry_after + 1)
                continue
                
            except BadRequest as e:
                error_msg = str(e).lower()
                if "message is not modified" in error_msg:
                    return None  # Content unchanged, not an error
                elif "message to edit not found" in error_msg:
                    return None
                elif "can't parse entities" in error_msg:
                    # Try without parse_mode
                    try:
                        return await self.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=text,
                            reply_markup=reply_markup,
                        )
                    except:
                        return None
                else:
                    logger.warning(f"BadRequest editing message: {e}")
                    return None
                    
            except TimedOut:
                logger.warning(f"Timeout editing message, attempt {attempt + 1}")
                await asyncio.sleep(1)
                continue
                
            except TelegramError as e:
                logger.error(f"Error editing message: {e}")
                return None
        
        return None
    
    async def safe_send_photo(
        self,
        chat_id: int,
        photo: io.BytesIO,
        caption: str = "",
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> Optional[Message]:
        """Send photo with flood wait protection"""
        for attempt in range(config.FLOOD_WAIT_MAX_RETRIES):
            try:
                await flood_protection.wait_if_needed(chat_id, "photo")
                photo.seek(0)  # Reset position
                message = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    reply_to_message_id=reply_to_message_id,
                )
                flood_protection.clear_flood_wait(chat_id)
                return message
                
            except RetryAfter as e:
                logger.warning(f"RetryAfter: {e.retry_after}s for photo in chat {chat_id}")
                flood_protection.handle_retry_after(chat_id, e.retry_after)
                await asyncio.sleep(e.retry_after + 1)
                continue
                
            except TimedOut:
                logger.warning(f"Timeout sending photo, attempt {attempt + 1}")
                await asyncio.sleep(2 ** attempt)
                continue
                
            except BadRequest as e:
                if "caption is too long" in str(e).lower():
                    # Try with shorter caption
                    short_caption = caption[:1024]
                    try:
                        return await self.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=short_caption,
                            reply_markup=reply_markup,
                        )
                    except:
                        return None
                logger.error(f"BadRequest sending photo: {e}")
                return None
                
            except TelegramError as e:
                logger.error(f"Error sending photo: {e}")
                if attempt < config.FLOOD_WAIT_MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    async def safe_send_chat_action(self, chat_id: int, action: str):
        """Send typing/uploading action"""
        try:
            await flood_protection.wait_if_needed(chat_id, "action")
            await self.bot.send_chat_action(chat_id=chat_id, action=action)
        except:
            pass  # Non-critical, don't break on errors
    
    async def safe_answer_callback(self, callback_query_id: str, text: str = ""):
        """Answer callback query"""
        try:
            await self.bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text,
            )
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await self.bot.answer_callback_query(
                    callback_query_id=callback_query_id,
                    text=text,
                )
            except:
                pass
        except:
            pass  # Non-critical


# ============================================================
# PROGRESS DISPLAY MANAGER
# ============================================================

class ProgressDisplayManager:
    """Manages progress display messages"""
    
    def __init__(self, telegram_api: SafeTelegramAPI):
        self.api = telegram_api
    
    async def send_initial_progress(
        self,
        chat_id: int,
        user_state: UserState,
        reply_to: Optional[int] = None,
    ) -> Optional[int]:
        """Send initial progress message"""
        progress = user_state.progress
        text = progress.get_full_display(user_state.prompt)
        
        # Add cancel button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ CANCEL", callback_data="cancel_process")]
        ])
        
        msg = await self.api.safe_send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            reply_to_message_id=reply_to,
        )
        
        if msg:
            user_state.last_progress_message_id = msg.message_id
            return msg.message_id
        return None
    
    async def update_progress(
        self,
        chat_id: int,
        user_state: UserState,
    ) -> bool:
        """Update existing progress message"""
        if not user_state.last_progress_message_id:
            return False
        
        progress = user_state.progress
        text = progress.get_full_display(user_state.prompt)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ CANCEL", callback_data="cancel_process")]
        ])
        
        result = await self.api.safe_edit_message(
            chat_id=chat_id,
            message_id=user_state.last_progress_message_id,
            text=text,
            reply_markup=keyboard,
        )
        
        return result is not None
    
    async def send_compact_update(
        self,
        chat_id: int,
        user_state: UserState,
    ):
        """Send compact progress update (new message if can't edit)"""
        progress = user_state.progress
        text = progress.get_compact_display(user_state.prompt)
        
        await self.api.safe_send_message(
            chat_id=chat_id,
            text=text,
        )


# ============================================================
# IMAGE PROCESSOR
# ============================================================

class ImageProcessor:
    """Handles image processing with Hugging Face API"""
    
    def __init__(self, telegram_api: SafeTelegramAPI, progress_display: ProgressDisplayManager):
        self.api = telegram_api
        self.progress_display = progress_display
    
    async def validate_image(self, image_bytes: bytes) -> tuple[bool, str, Optional[bytes]]:
        """Validate and process image"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Check format
            if img.format not in ['JPEG', 'PNG', 'WEBP']:
                return False, "Unsupported format. Please send JPEG, PNG, or WEBP.", None
            
            # Resize if too large
            if img.size[0] > config.MAX_IMAGE_SIZE[0] or img.size[1] > config.MAX_IMAGE_SIZE[1]:
                img.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            processed_bytes = output.getvalue()
            
            return True, "Image validated successfully", processed_bytes
            
        except Exception as e:
            return False, f"Invalid image: {str(e)}", None
    
    def enhance_prompt(self, prompt: str) -> tuple[str, str]:
        """Enhance prompt for better face consistency"""
        # Positive prompt
        enhanced = (
            f"{prompt}, "
            "maintain exact same face, face consistency, same person identity, "
            "photorealistic, high quality, detailed"
        )
        
        # Negative prompt
        negative = (
            "different face, different person, deformed face, ugly, blurry, "
            "bad quality, watermark, text, logo, low resolution, "
            "extra limbs, mutated hands, poorly drawn face"
        )
        
        return enhanced, negative
    
    async def call_hf_api(
        self,
        image_bytes: bytes,
        prompt: str,
        negative_prompt: str,
        user_state: UserState,
        chat_id: int,
    ) -> Optional[bytes]:
        """Call Hugging Face API with progress updates"""
        
        if not config.HF_TOKEN:
            raise Exception("HUGGINGFACE_TOKEN not configured!")
        
        headers = {"Authorization": f"Bearer {config.HF_TOKEN}"}
        progress = user_state.progress
        
        # Prepare image
        progress.set_stage(ProcessStage.PREPARING_API_REQUEST)
        await self.progress_display.update_progress(chat_id, user_state)
        
        img = Image.open(io.BytesIO(image_bytes))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_bytes = img_byte_arr.getvalue()
        
        # Try multiple API approaches
        for api_attempt in range(3):
            progress.api_call_count += 1
            
            # Stage: Uploading
            progress.set_stage(ProcessStage.UPLOADING_IMAGE)
            await self.progress_display.update_progress(chat_id, user_state)
            
            try:
                async with httpx.AsyncClient(timeout=config.API_TIMEOUT) as client:
                    
                    # Approach 1: Binary image input (most compatible)
                    if api_attempt == 0:
                        logger.info(f"API attempt 1: Binary input for user {user_state.user_id}")
                        
                        progress.set_stage(ProcessStage.AI_PROCESSING)
                        await self.progress_display.update_progress(chat_id, user_state)
                        
                        response = await client.post(
                            f"{config.HF_BASE_URL}/{config.HF_MODEL}",
                            headers={
                                **headers,
                                "Content-Type": "image/jpeg",
                            },
                            content=img_bytes,
                            params={
                                "prompt": prompt,
                                "negative_prompt": negative_prompt,
                            }
                        )
                    
                    # Approach 2: Form data
                    elif api_attempt == 1:
                        logger.info(f"API attempt 2: Form data for user {user_state.user_id}")
                        
                        progress.set_stage(ProcessStage.AI_PROCESSING)
                        await self.progress_display.update_progress(chat_id, user_state)
                        
                        response = await client.post(
                            f"{config.HF_BASE_URL}/{config.HF_MODEL}",
                            headers=headers,
                            files={"image": ("image.jpg", img_bytes, "image/jpeg")},
                            data={
                                "prompt": prompt,
                                "negative_prompt": negative_prompt,
                            }
                        )
                    
                    # Approach 3: JSON with base64
                    else:
                        logger.info(f"API attempt 3: JSON base64 for user {user_state.user_id}")
                        import base64
                        
                        progress.set_stage(ProcessStage.AI_PROCESSING)
                        await self.progress_display.update_progress(chat_id, user_state)
                        
                        response = await client.post(
                            f"{config.HF_BASE_URL}/{config.HF_MODEL}",
                            headers=headers,
                            json={
                                "inputs": prompt,
                                "parameters": {
                                    "negative_prompt": negative_prompt,
                                    "image": base64.b64encode(img_bytes).decode(),
                                    "strength": config.IMG2IMG_STRENGTH,
                                    "guidance_scale": config.GUIDANCE_SCALE,
                                    "num_inference_steps": config.INFERENCE_STEPS,
                                }
                            }
                        )
                    
                    # Check response
                    if response.status_code == 200:
                        progress.set_stage(ProcessStage.DOWNLOADING_RESULT)
                        await self.progress_display.update_progress(chat_id, user_state)
                        
                        content_type = response.headers.get("content-type", "")
                        if "image" in content_type:
                            return response.content
                        else:
                            logger.warning(f"Unexpected content type: {content_type}")
                            return response.content
                    
                    elif response.status_code == 503:
                        # Model loading
                        logger.warning("Model is loading, waiting...")
                        progress.set_stage(
                            ProcessStage.AI_PROCESSING,
                            "Model is loading, please wait..."
                        )
                        await self.progress_display.update_progress(chat_id, user_state)
                        await asyncio.sleep(10)
                        progress.retry_count += 1
                        continue
                    
                    elif response.status_code == 429:
                        # Rate limited
                        logger.warning("Rate limited by HuggingFace")
                        await asyncio.sleep(15)
                        progress.retry_count += 1
                        continue
                    
                    else:
                        error_text = response.text[:200]
                        logger.warning(f"API returned {response.status_code}: {error_text}")
                        
                        if api_attempt < 2:
                            await asyncio.sleep(5)
                            progress.retry_count += 1
                            continue
                        else:
                            raise Exception(f"API error: {response.status_code}")
                            
            except httpx.TimeoutException:
                logger.warning(f"API timeout, attempt {api_attempt + 1}")
                if api_attempt < 2:
                    progress.retry_count += 1
                    continue
                else:
                    raise Exception("API request timed out")
            
            except Exception as e:
                if api_attempt < 2:
                    logger.warning(f"API attempt {api_attempt + 1} failed: {e}")
                    progress.retry_count += 1
                    await asyncio.sleep(3)
                    continue
                else:
                    raise
        
        return None
    
    async def process_image(
        self,
        chat_id: int,
        user_state: UserState,
    ) -> tuple[bool, Optional[bytes], str]:
        """Main image processing pipeline"""
        progress = user_state.progress
        
        try:
            # Stage: Validating
            progress.set_stage(ProcessStage.VALIDATING_IMAGE)
            await self.progress_display.update_progress(chat_id, user_state)
            
            is_valid, message, processed_bytes = await self.validate_image(user_state.image_bytes)
            if not is_valid:
                return False, None, message
            
            user_state.image_bytes = processed_bytes
            
            # Small delay for visual progress
            await asyncio.sleep(0.5)
            
            # Stage: Processing prompt
            progress.set_stage(ProcessStage.PROCESSING_PROMPT)
            await self.progress_display.update_progress(chat_id, user_state)
            
            enhanced_prompt, negative_prompt = self.enhance_prompt(user_state.prompt)
            
            await asyncio.sleep(0.5)
            
            # Call API
            result = await self.call_hf_api(
                processed_bytes,
                enhanced_prompt,
                negative_prompt,
                user_state,
                chat_id,
            )
            
            if result is None:
                return False, None, "Failed to get result from AI. Please try again."
            
            # Stage: Post processing
            progress.set_stage(ProcessStage.POST_PROCESSING)
            await self.progress_display.update_progress(chat_id, user_state)
            
            # Validate result is an image
            try:
                result_img = Image.open(io.BytesIO(result))
                result_img.verify()
                
                # Re-open for saving (verify closes the image)
                result_img = Image.open(io.BytesIO(result))
                output = io.BytesIO()
                result_img.save(output, format='JPEG', quality=90)
                final_bytes = output.getvalue()
                
            except Exception as e:
                logger.warning(f"Result validation failed: {e}")
                # Try to return raw result anyway
                final_bytes = result
            
            return True, final_bytes, "Success!"
            
        except Exception as e:
            logger.error(f"Processing error: {traceback.format_exc()}")
            return False, None, str(e)


# ============================================================
# BOT HANDLERS
# ============================================================

class BotHandlers:
    """All bot command and message handlers"""
    
    def __init__(self):
        self.telegram_api: Optional[SafeTelegramAPI] = None
        self.progress_display: Optional[ProgressDisplayManager] = None
        self.image_processor: Optional[ImageProcessor] = None
    
    def initialize(self, application: Application):
        """Initialize handlers with application context"""
        self.telegram_api = SafeTelegramAPI(application)
        self.progress_display = ProgressDisplayManager(self.telegram_api)
        self.image_processor = ImageProcessor(self.telegram_api, self.progress_display)
    
    # ----------------------------------------------------------
    # COMMAND HANDLERS
    # ----------------------------------------------------------
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_state = await user_manager.get_or_create(user.id)
        user_state.reset()
        
        welcome_text = f"""
╔══════════════════════════════════════╗
║      🤖 AI IMAGE EDITOR BOT         ║
╚══════════════════════════════════════╝

👋 **Welcome {user.first_name}!**

I can edit your photos using AI while keeping the face **EXACTLY THE SAME!**

**📋 HOW TO USE:**
━━━━━━━━━━━━━━━━━━━━━━━
1️⃣ Send me a **PHOTO** (with clear face)
2️⃣ Choose a **preset** or write **custom prompt**
3️⃣ Watch the **progress** as AI processes
4️⃣ Receive your **edited image!**

**🎯 PRESETS AVAILABLE:**
━━━━━━━━━━━━━━━━━━━━━━━
🌅 Background Change
🎨 Artistic Style
😎 Add Accessories
✍️ Custom Prompt

**💡 TIPS FOR BEST RESULTS:**
━━━━━━━━━━━━━━━━━━━━━━━
• Use front-facing photos
• Ensure good lighting
• Face should be clearly visible

**⚡ COMMANDS:**
━━━━━━━━━━━━━━━━━━━━━━━
/start - Start the bot
/help - Show help
/cancel - Cancel current operation
/status - Check current status

👇 **Send a photo to begin!**
"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help", callback_data="cmd_help"),
                InlineKeyboardButton("🎯 Examples", callback_data="cmd_examples"),
            ],
            [
                InlineKeyboardButton("🔄 Reset", callback_data="cmd_reset"),
            ],
        ])
        
        await self.telegram_api.safe_send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text,
            reply_markup=keyboard,
            reply_to_message_id=update.message.message_id,
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
╔══════════════════════════════════════╗
║           📖 HELP GUIDE             ║
╚══════════════════════════════════════╝

**🚀 QUICK START:**
━━━━━━━━━━━━━━━━━━━━━━━
1. Send a photo with a visible face
2. Choose what you want to change
3. Wait for AI to process (30-120 sec)
4. Get your edited photo!

**🎯 PRESET OPTIONS:**
━━━━━━━━━━━━━━━━━━━━━━━
• **Background Change** - Change the background scene
• **Artistic Style** - Apply painting/art effects
• **Add Accessories** - Add sunglasses, hats, etc.
• **Custom Prompt** - Write your own description

**✍️ CUSTOM PROMPT EXAMPLES:**
━━━━━━━━━━━━━━━━━━━━━━━
• "Change background to sunset beach"
• "Make it look like a Renaissance painting"
• "Add a cowboy hat"
• "Change hair color to blonde"
• "Make it look professional for LinkedIn"
• "Transform into anime style"

**⚠️ IMPORTANT NOTES:**
━━━━━━━━━━━━━━━━━━━━━━━
• Face will stay EXACTLY the same
• Processing takes 30-120 seconds
• Best results with clear, front-facing photos
• Free API may have occasional delays

**🔧 COMMANDS:**
━━━━━━━━━━━━━━━━━━━━━━━
/start - Restart the bot
/help - This message
/cancel - Cancel current operation
/status - Check processing status

**❓ PROBLEMS?**
━━━━━━━━━━━━━━━━━━━━━━━
• Bot not responding? Wait 30 seconds
• Photo not processing? Try /cancel and resend
• Face changed? Use more specific prompt
"""
        await self.telegram_api.safe_send_message(
            chat_id=update.effective_chat.id,
            text=help_text,
            reply_to_message_id=update.message.message_id if update.message else None,
        )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        user = update.effective_user
        await user_manager.reset(user.id)
        
        await self.telegram_api.safe_send_message(
            chat_id=update.effective_chat.id,
            text="✅ **Operation cancelled.**\n\nSend a new photo to start again!",
            reply_to_message_id=update.message.message_id if update.message else None,
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user
        user_state = await user_manager.get(user.id)
        
        if not user_state or user_state.state == "idle":
            await self.telegram_api.safe_send_message(
                chat_id=update.effective_chat.id,
                text="⚪ **Status: IDLE**\n\nNo active processing. Send a photo to start!",
                reply_to_message_id=update.message.message_id,
            )
        else:
            progress = user_state.progress
            text = progress.get_full_display(user_state.prompt)
            await self.telegram_api.safe_send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_to_message_id=update.message.message_id,
            )
    
    # ----------------------------------------------------------
    # PHOTO HANDLER
    # ----------------------------------------------------------
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming photos"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        logger.info(f"Photo received from {user.first_name} (ID: {user.id})")
        
        # Get user state
        user_state = await user_manager.get_or_create(user.id)
        
        # Check if already processing
        if user_state.state == "processing":
            await self.telegram_api.safe_send_message(
                chat_id=chat_id,
                text="⚠️ **Already processing!**\n\nPlease wait or type /cancel to stop current operation.",
                reply_to_message_id=update.message.message_id,
            )
            return
        
        # Reset state
        user_state.reset()
        
        # Get photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download photo
        photo_bytes = io.BytesIO()
        await file.download_to_memory(photo_bytes)
        photo_bytes.seek(0)
        
        # Store in state
        user_state.image_bytes = photo_bytes.getvalue()
        user_state.file_id = photo.file_id
        user_state.state = "waiting_prompt"
        user_state.progress.set_stage(ProcessStage.RECEIVED_IMAGE)
        
        # Send confirmation with options
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🌅 Background Change", callback_data="preset_bg"),
                InlineKeyboardButton("🎨 Artistic Style", callback_data="preset_art"),
            ],
            [
                InlineKeyboardButton("😎 Add Accessories", callback_data="preset_acc"),
                InlineKeyboardButton("✍️ Custom Prompt", callback_data="preset_custom"),
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_process"),
            ],
        ])
        
        await self.telegram_api.safe_send_message(
            chat_id=chat_id,
            text=(
                "╔══════════════════════════════════════╗\n"
                "║       📸 IMAGE RECEIVED!             ║\n"
                "╚══════════════════════════════════════╝\n\n"
                "✅ **Photo successfully received!**\n\n"
                f"📏 **Size:** {photo.width}x{photo.height}\n\n"
                "👇 **Choose what you want to do:**\n\n"
                "🌅 **Background Change** - Change the scene\n"
                "🎨 **Artistic Style** - Apply art effects\n"
                "😎 **Add Accessories** - Sunglasses, hats, etc.\n"
                "✍️ **Custom Prompt** - Write your own description"
            ),
            reply_markup=keyboard,
            reply_to_message_id=update.message.message_id,
        )
    
    # ----------------------------------------------------------
    # CALLBACK HANDLERS
    # ----------------------------------------------------------
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries (buttons)"""
        query = update.callback_query
        user = query.from_user
        chat_id = query.message.chat_id
        
        # ALWAYS answer callback first to prevent loading indicator
        await self.telegram_api.safe_answer_callback(query.id)
        
        logger.info(f"Callback from {user.first_name}: {query.data}")
        
        # Get user state
        user_state = await user_manager.get_or_create(user.id)
        
        # Route to appropriate handler
        data = query.data
        
        if data == "cancel_process":
            await self._handle_cancel(query, user_state, chat_id)
        elif data.startswith("preset_"):
            await self._handle_preset(query, user_state, chat_id, data)
        elif data == "cmd_help":
            await self._handle_cmd_help(query, chat_id)
        elif data == "cmd_examples":
            await self._handle_cmd_examples(query, chat_id)
        elif data == "cmd_reset":
            await self._handle_cmd_reset(query, user_state, chat_id)
        elif data == "back_to_presets":
            await self._handle_back_to_presets(query, user_state, chat_id)
        elif data == "back_to_main":
            await self._handle_back_to_main(query, chat_id)
        else:
            logger.warning(f"Unknown callback data: {data}")
    
    async def _handle_cancel(self, query: CallbackQuery, user_state: UserState, chat_id: int):
        """Handle cancel button"""
        user_state.reset()
        await self.telegram_api.safe_edit_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=(
                "❌ **Operation Cancelled**\n\n"
                "All processing stopped.\n\n"
                "Send a new photo to start again! 📸"
            ),
        )
    
    async def _handle_preset(self, query: CallbackQuery, user_state: UserState, chat_id: int, data: str):
        """Handle preset selection"""
        # Check state
        if user_state.state != "waiting_prompt":
            await self.telegram_api.safe_edit_message(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text="⚠️ **Please send a photo first!**\n\n/start to begin",
            )
            return
        
        # Map presets to prompts
        presets = {
            "preset_bg": {
                "prompt": "Change the background to a beautiful sunset beach scene with golden light, keep the person and face exactly the same",
                "name": "Background Change",
                "emoji": "🌅",
            },
            "preset_art": {
                "prompt": "Transform into a beautiful detailed oil painting style, maintain exact same face features and identity",
                "name": "Artistic Style",
                "emoji": "🎨",
            },
            "preset_acc": {
                "prompt": "Add cool stylish sunglasses on the face, keep everything else exactly the same, photorealistic",
                "name": "Add Accessories",
                "emoji": "😎",
            },
            "preset_custom": {
                "prompt": None,
                "name": "Custom Prompt",
                "emoji": "✍️",
            },
        }
        
        preset = presets.get(data)
        if not preset:
            return
        
        # Handle custom prompt
        if preset["prompt"] is None:
            user_state.state = "waiting_custom_prompt"
            user_state.prompt_type = "custom"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back to Presets", callback_data="back_to_presets")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_process")],
            ])
            
            await self.telegram_api.safe_edit_message(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text=(
                    "╔══════════════════════════════════════╗\n"
                    "║       ✍️ CUSTOM PROMPT              ║\n"
                    "╚══════════════════════════════════════╝\n\n"
                    "📝 **Type your editing prompt below:**\n\n"
                    "**EXAMPLES:**\n"
                    "• \"Change background to mountain view\"\n"
                    "• \"Make it look like a superhero\"\n"
                    "• \"Add a formal suit\"\n"
                    "• \"Change hair to curly red\"\n"
                    "• \"Transform into anime character\"\n\n"
                    "💡 **TIP:** Be specific and mention\n"
                    "\"keep face same\" for best results!\n\n"
                    "👇 **Type your prompt now:**"
                ),
                reply_markup=keyboard,
            )
            return
        
        # Apply preset
        user_state.prompt = preset["prompt"]
        user_state.prompt_type = data
        user_state.state = "processing"
        
        # Start processing
        await self._start_processing(query, user_state, chat_id, preset)
    
    async def _handle_cmd_help(self, query: CallbackQuery, chat_id: int):
        """Handle help button"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")],
        ])
        
        help_text = (
            "╔══════════════════════════════════════╗\n"
            "║           📖 QUICK HELP              ║\n"
            "╚══════════════════════════════════════╝\n\n"
            "**🎯 HOW TO USE:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. Send a photo with face\n"
            "2. Choose preset or custom\n"
            "3. Wait for AI processing\n"
            "4. Get edited photo!\n\n"
            "**💡 BEST RESULTS:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• Front-facing photos\n"
            "• Good lighting\n"
            "• Specific prompts\n"
            "• Mention \"keep face same\"\n\n"
            "**⏱️ TIMING:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• Processing: 30-120 seconds\n"
            "• First time may be slower\n\n"
            "**🔧 COMMANDS:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "/start - Restart bot\n"
            "/help - Full help\n"
            "/cancel - Cancel operation\n"
            "/status - Check status"
        )
        
        await self.telegram_api.safe_edit_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=help_text,
            reply_markup=keyboard,
        )
    
    async def _handle_cmd_examples(self, query: CallbackQuery, chat_id: int):
        """Handle examples button"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")],
        ])
        
        examples_text = (
            "╔══════════════════════════════════════╗\n"
            "║         🎯 PROMPT EXAMPLES           ║\n"
            "╚══════════════════════════════════════╝\n\n"
            "**🌅 BACKGROUNDS:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• \"Change background to sunset beach\"\n"
            "• \"Put me in a forest\"\n"
            "• \"Background: city skyline at night\"\n\n"
            "**🎨 STYLES:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• \"Make it oil painting\"\n"
            "• \"Transform to anime style\"\n"
            "• \"Watercolor painting effect\"\n"
            "• \"Cyberpunk neon style\"\n\n"
            "**😎 ACCESSORIES:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• \"Add sunglasses\"\n"
            "• \"Add cowboy hat\"\n"
            "• \"Add formal tie\"\n\n"
            "**👔 OUTFITS:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• \"Wear a business suit\"\n"
            "• \"Superhero costume\"\n"
            "• \"Traditional Indian attire\"\n\n"
            "**💡 PRO TIP:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Always add \"keep face same\" for\n"
            "best face consistency!"
        )
        
        await self.telegram_api.safe_edit_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=examples_text,
            reply_markup=keyboard,
        )
    
    async def _handle_cmd_reset(self, query: CallbackQuery, user_state: UserState, chat_id: int):
        """Handle reset button"""
        user_state.reset()
        await self.telegram_api.safe_edit_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=(
                "✅ **Bot Reset Complete!**\n\n"
                "All data cleared. Send a new photo to start! 📸"
            ),
        )
    
    async def _handle_back_to_presets(self, query: CallbackQuery, user_state: UserState, chat_id: int):
        """Handle back to presets button"""
        user_state.state = "waiting_prompt"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🌅 Background Change", callback_data="preset_bg"),
                InlineKeyboardButton("🎨 Artistic Style", callback_data="preset_art"),
            ],
            [
                InlineKeyboardButton("😎 Add Accessories", callback_data="preset_acc"),
                InlineKeyboardButton("✍️ Custom Prompt", callback_data="preset_custom"),
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_process"),
            ],
        ])
        
        await self.telegram_api.safe_edit_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=(
                "╔══════════════════════════════════════╗\n"
                "║       📸 CHOOSE OPTION               ║\n"
                "╚══════════════════════════════════════╝\n\n"
                "👇 **Choose what you want to do:**\n\n"
                "🌅 **Background Change**\n"
                "🎨 **Artistic Style**\n"
                "😎 **Add Accessories**\n"
                "✍️ **Custom Prompt**"
            ),
            reply_markup=keyboard,
        )
    
    async def _handle_back_to_main(self, query: CallbackQuery, chat_id: int):
        """Handle back to main button"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help", callback_data="cmd_help"),
                InlineKeyboardButton("🎯 Examples", callback_data="cmd_examples"),
            ],
            [
                InlineKeyboardButton("🔄 Reset", callback_data="cmd_reset"),
            ],
        ])
        
        await self.telegram_api.safe_edit_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=(
                "╔══════════════════════════════════════╗\n"
                "║      🤖 AI IMAGE EDITOR BOT         ║\n"
                "╚══════════════════════════════════════╝\n\n"
                "Send me a **PHOTO** to start editing!\n\n"
                "**📋 OPTIONS:**\n"
                "• 🌅 Background Change\n"
                "• 🎨 Artistic Style\n"
                "• 😎 Add Accessories\n"
                "• ✍️ Custom Prompt\n\n"
                "👇 **Send a photo to begin!**"
            ),
            reply_markup=keyboard,
        )
    
    # ----------------------------------------------------------
    # TEXT HANDLER (for custom prompts)
    # ----------------------------------------------------------
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        text = update.message.text
        
        # Get user state
        user_state = await user_manager.get_or_create(user.id)
        
        # Check state
        if user_state.state == "idle":
            await self.telegram_api.safe_send_message(
                chat_id=chat_id,
                text="📸 **Send a photo first!**\n\nType /start to begin.",
                reply_to_message_id=update.message.message_id,
            )
            return
        
        if user_state.state == "processing":
            await self.telegram_api.safe_send_message(
                chat_id=chat_id,
                text="⏳ **Processing in progress!**\n\nPlease wait or type /cancel.",
                reply_to_message_id=update.message.message_id,
            )
            return
        
        if user_state.state not in ["waiting_prompt", "waiting_custom_prompt"]:
            await self.telegram_api.safe_send_message(
                chat_id=chat_id,
                text="📸 **Unexpected input.**\n\nSend a photo or type /start.",
                reply_to_message_id=update.message.message_id,
            )
            return
        
        # Store prompt
        user_state.prompt = text
        user_state.state = "processing"
        
        # Send confirmation
        await self.telegram_api.safe_send_message(
            chat_id=chat_id,
            text=(
                f"✅ **Prompt received!**\n\n"
                f"✏️ **Your prompt:**\n_{text}_\n\n"
                f"🚀 Starting AI processing..."
            ),
            reply_to_message_id=update.message.message_id,
        )
        
        # Start processing
        preset_info = {"name": "Custom", "emoji": "✍️"}
        await self._start_processing_from_state(user_state, chat_id, preset_info)
    
    # ----------------------------------------------------------
    # IMAGE PROCESSING PIPELINE
    # ----------------------------------------------------------
    
    async def _start_processing(self, query: CallbackQuery, user_state: UserState, chat_id: int, preset_info: dict):
        """Start image processing from button callback"""
        # Edit message to show processing started
        await self.telegram_api.safe_edit_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=(
                f"✅ **{preset_info['emoji']} {preset_info['name']} Selected!**\n\n"
                f"✏️ **Prompt:** _{user_state.prompt[:100]}{'...' if len(user_state.prompt) > 100 else ''}_\n\n"
                f"🚀 **Starting AI processing...**"
            ),
        )
        
        await asyncio.sleep(1)
        
        # Start processing
        await self._run_processing(user_state, chat_id)
    
    async def _start_processing_from_state(self, user_state: UserState, chat_id: int, preset_info: dict):
        """Start processing from text input"""
        await asyncio.sleep(0.5)
        await self._run_processing(user_state, chat_id)
    
    async def _run_processing(self, user_state: UserState, chat_id: int):
        """Run the actual image processing"""
        progress = user_state.progress
        progress.start_time = time.time()
        
        # Initialize progress
        progress.set_stage(ProcessStage.VALIDATING_IMAGE)
        
        # Send initial progress message
        await self.progress_display.send_initial_progress(
            chat_id=chat_id,
            user_state=user_state,
        )
        
        # Process image
        success, result_bytes, message = await self.image_processor.process_image(
            chat_id=chat_id,
            user_state=user_state,
        )
        
        if success and result_bytes:
            # Stage: Sending result
            progress.set_stage(ProcessStage.SENDING_RESULT)
            await self.progress_display.update_progress(chat_id, user_state)
            
            # Send result
            result_stream = io.BytesIO(result_bytes)
            
            caption = (
                f"✅ **Image Editing Complete!**\n\n"
                f"✏️ **Prompt:** _{user_state.prompt[:100]}{'...' if len(user_state.prompt) > 100 else ''}_\n\n"
                f"⏱️ **Total Time:** {progress.get_elapsed_time()}\n"
                f"🔄 **API Calls:** {progress.api_call_count}\n"
                f"🔁 **Retries:** {progress.retry_count}\n\n"
                f"📸 **Send another photo to edit more!**"
            )
            
            # Keyboard for result
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Edit Again", callback_data="back_to_main"),
                    InlineKeyboardButton("📖 Help", callback_data="cmd_help"),
                ],
            ])
            
            await self.telegram_api.safe_send_photo(
                chat_id=chat_id,
                photo=result_stream,
                caption=caption,
                reply_markup=keyboard,
            )
            
            # Update progress to complete
            progress.set_stage(ProcessStage.COMPLETE)
            await self.progress_display.update_progress(chat_id, user_state)
            
            logger.info(f"Processing complete for user {user_state.user_id} in {progress.get_elapsed_time()}")
            
        else:
            # Error
            progress.set_stage(ProcessStage.ERROR, message)
            await self.progress_display.update_progress(chat_id, user_state)
            
            # Send error with retry option
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Try Again", callback_data="back_to_presets"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_process"),
                ],
            ])
            
            error_text = (
                f"╔══════════════════════════════════════╗\n"
                f"║         ❌ PROCESSING FAILED         ║\n"
                f"╚══════════════════════════════════════╝\n\n"
                f"**Error:** {message}\n\n"
                f"**Possible reasons:**\n"
                f"• API server overloaded\n"
                f"• Image format issue\n"
                f"• Network timeout\n\n"
                f"**What to do:**\n"
                f"• Wait a few minutes and try again\n"
                f"• Use a different photo\n"
                f"• Try a simpler prompt\n\n"
                f"⏱️ **Time elapsed:** {progress.get_elapsed_time()}\n"
                f"🔄 **Attempts:** {progress.api_call_count}"
            )
            
            await self.telegram_api.safe_send_message(
                chat_id=chat_id,
                text=error_text,
                reply_markup=keyboard,
            )
        
        # Reset state
        user_state.reset()


# ============================================================
# BACKGROUND TASKS
# ============================================================

async def cleanup_task():
    """Periodic cleanup of old user states"""
    while True:
        await asyncio.sleep(3600)  # Every hour
        await user_manager.cleanup_old(max_age=7200)  # Remove states older than 2 hours
        logger.info("Periodic cleanup completed")


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main entry point"""
    # Validate configuration
    if not config.TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        print("\n❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
        print("Set it in .env file or as environment variable")
        sys.exit(1)
    
    if not config.HF_TOKEN:
        logger.warning("HUGGINGFACE_TOKEN not set - API calls will fail!")
        print("\n⚠️ WARNING: HUGGINGFACE_TOKEN not set!")
        print("Get FREE token at: https://huggingface.co/settings/tokens")
    
    # Create handlers
    handlers = BotHandlers()
    
    # Create application
    application = (
        Application.builder()
        .token(config.TELEGRAM_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Initialize handlers
    handlers.initialize(application)
    
    # Add handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("cancel", handlers.cancel_command))
    application.add_handler(CommandHandler("status", handlers.status_command))
    
    # Photo handler
    application.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    
    # Callback handler (buttons)
    application.add_handler(CallbackQueryHandler(handlers.handle_callback))
    
    # Text handler (for custom prompts)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    
    # Error handler
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error: {context.error}")
        logger.error(traceback.format_exc())
        
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "⚠️ **An error occurred!**\n\n"
                        "The bot encountered an error. Please try again.\n\n"
                        "Type /cancel to reset or /start to begin again."
                    ),
                )
            except:
                pass
    
    application.add_error_handler(error_handler)
    
    # Post init callback
    async def post_init(app: Application):
        """Run after initialization"""
        logger.info("=" * 50)
        logger.info("🤖 AI Image Editor Bot Started!")
        logger.info(f"📊 HF Token: {'✅ Set' if config.HF_TOKEN else '❌ Not Set'}")
        logger.info(f"📊 Max Retries: {config.FLOOD_WAIT_MAX_RETRIES}")
        logger.info(f"📊 API Timeout: {config.API_TIMEOUT}s")
        logger.info("=" * 50)
        
        # Start cleanup task
        asyncio.create_task(cleanup_task())
    
    application.post_init = post_init
    
    # Run bot
    logger.info("Starting bot polling...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
