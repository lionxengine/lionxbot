import asyncio
import logging
import os
import aiohttp
import json
import random
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton, InputMediaVideo

# Telegram file IDs (more reliable than URLs)
MAIN_MENU_VIDEO = "BAACAgQAAxkBAAIsNmq_jRh7kV0y76e8jrAGZvxIj14dAAIJHQAC2kH4URTOucxJcpJlPQQ"
WELCOME_VIDEO = "BAACAgQAAxkBAAIsOmq_jYRDly0AAbeqnvamMAyHSD1llwACAyEAAsrPAAFSgzrU1wyCnUo9BA"

TOKEN = "8753339785:AAFNUMnfnI89EpzxdGJf7Zs1MOaDMiLUYi8"

# Config
CHANNEL_USERNAME = "LionX_Engine"
CHANNEL_URL = "https://t.me/LionX_Engine"
RESELLER_NAME = "Khalid Khan"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Firebase config from panel
FIREBASE_PROJECT_ID = "lionengine"
FIREBASE_API_KEY = "AIzaSyCzfbotjRCNYM2j_wRwICU03cx6EbKjWfE"
FIREBASE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"

# Maintenance mode state (in-memory, can be moved to Firestore if needed)
maintenance_mode = False

class FirebaseClient:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _doc_to_dict(self, doc):
        if not doc or 'fields' not in doc:
            return {}
        result = {}
        for key, value in doc['fields'].items():
            if 'stringValue' in value:
                result[key] = value['stringValue']
            elif 'integerValue' in value:
                result[key] = int(value['integerValue'])
            elif 'doubleValue' in value:
                result[key] = float(value['doubleValue'])
            elif 'booleanValue' in value:
                result[key] = value['booleanValue']
            elif 'timestampValue' in value:
                result[key] = value['timestampValue']
            elif 'nullValue' in value:
                result[key] = None
            elif 'mapValue' in value:
                result[key] = self._doc_to_dict({'fields': value['mapValue']})
            elif 'arrayValue' in value:
                result[key] = [self._doc_to_dict({'fields': {'v': v}})['v'] for v in value['arrayValue'].get('values', [])]
            else:
                result[key] = None
        return result
    
    def _to_firestore_value(self, value):
        if value is None:
            return {'nullValue': None}
        elif isinstance(value, str):
            return {'stringValue': value}
        elif isinstance(value, bool):
            return {'booleanValue': value}
        elif isinstance(value, int):
            return {'integerValue': str(value)}
        elif isinstance(value, float):
            return {'doubleValue': value}
        elif isinstance(value, datetime):
            return {'timestampValue': value.isoformat() + 'Z'}
        elif isinstance(value, dict):
            return {'mapValue': {'fields': {k: self._to_firestore_value(v) for k, v in value.items()}}}
        elif isinstance(value, list):
            return {'arrayValue': {'values': [self._to_firestore_value(v) for v in value]}}
        else:
            return {'stringValue': str(value)}
    
    async def get_user(self, user_id: int, first_name: str = None, username: str = None):
        session = await self.get_session()
        doc_path = f"{FIREBASE_BASE_URL}/users/{user_id}?key={FIREBASE_API_KEY}"
        
        async with session.get(doc_path) as resp:
            if resp.status == 200:
                doc = await resp.json()
                return self._doc_to_dict(doc)
            elif resp.status == 404:
                member_since = datetime.now().strftime("%Y-%m-%d")
                user_data = {
                    'fields': {
                        'user_id': {'integerValue': str(user_id)},
                        'first_name': {'stringValue': first_name or "User"},
                        'username': {'stringValue': username or ""},
                        'points': {'doubleValue': 0.0},
                        'streak': {'integerValue': '0'},
                        'last_streak_date': {'nullValue': None},
                        'high_streak': {'integerValue': '0'},
                        'total_invites': {'integerValue': '0'},
                        'total_keys': {'integerValue': '0'},
                        'daily_key_claimed_at': {'nullValue': None},
                        'invited_users': {'arrayValue': {'values': []}},
                        'member_since': {'stringValue': member_since},
                        'created_at': {'timestampValue': datetime.now(timezone.utc).isoformat()}
                    }
                }
                async with session.patch(doc_path, json=user_data) as create_resp:
                    if create_resp.status in (200, 201):
                        return {
                            'user_id': user_id,
                            'first_name': first_name or "User",
                            'username': username or "",
                            'points': 0.0,
                            'streak': 0,
                            'last_streak_date': None,
                            'high_streak': 0,
                            'total_invites': 0,
                            'total_keys': 0,
                            'daily_key_claimed_at': None,
                            'invited_users': [],
                            'member_since': member_since
                        }
            return {
                'user_id': user_id,
                'first_name': first_name or "User",
                'username': username or "",
                'points': 0.0,
                'streak': 0,
                'last_streak_date': None,
                'high_streak': 0,
                'total_invites': 0,
                'total_keys': 0,
                'daily_key_claimed_at': None,
                'invited_users': [],
                'member_since': datetime.now().strftime("%Y-%m-%d")
            }
    
    async def update_user(self, user_id: int, updates: dict):
        session = await self.get_session()
        doc_path = f"{FIREBASE_BASE_URL}/users/{user_id}?key={FIREBASE_API_KEY}"
        
        # Check if any field needs increment
        transform_fields = {}
        regular_updates = {}
        
        for k, v in updates.items():
            if k.endswith('_increment') and v is True:
                field_name = k.replace('_increment', '')
                transform_fields[field_name] = {'increment': {'integerValue': '1'}}
            else:
                regular_updates[k] = v
        
        # Handle regular updates
        if regular_updates:
            update_mask = '&'.join([f'updateMask.fieldPaths={k}' for k in regular_updates.keys()])
            fields = {}
            for k, v in regular_updates.items():
                if isinstance(v, float):
                    fields[k] = {'doubleValue': v}
                elif isinstance(v, int) and not isinstance(v, bool):
                    fields[k] = {'integerValue': str(v)}
                elif isinstance(v, str):
                    fields[k] = {'stringValue': v}
                elif isinstance(v, bool):
                    fields[k] = {'booleanValue': v}
                elif isinstance(v, datetime):
                    fields[k] = {'timestampValue': v.isoformat()}
                elif v is None:
                    fields[k] = {'nullValue': None}
                elif isinstance(v, list):
                    fields[k] = {'arrayValue': {'values': [{'stringValue': str(item)} for item in v]}}
                else:
                    fields[k] = {'stringValue': str(v)}
            
            data = {'fields': fields}
            if transform_fields:
                data['transform'] = [{'fieldPath': k, 'increment': v} for k, v in transform_fields.items()]
            
            async with session.patch(f"{doc_path}&{update_mask}", json=data) as resp:
                if resp.status != 200:
                    logging.error(f"Update user failed: {await resp.text()}")
        elif transform_fields:
            # Only transforms, no regular updates
            data = {
                'transform': [{'fieldPath': k, 'increment': v} for k, v in transform_fields.items()]
            }
            async with session.patch(f"{doc_path}?key={FIREBASE_API_KEY}", json=data) as resp:
                if resp.status != 200:
                    logging.error(f"Update user transform failed: {await resp.text()}")
    
    async def update_user_points(self, user_id: int, points_change: float):
        user = await self.get_user(user_id)
        current = user.get('points', 0)
        await self.update_user(user_id, {'points': current + points_change})
    
    async def update_streak(self, user_id: int):
        today = datetime.now().date()
        today_str = today.isoformat()
        
        user = await self.get_user(user_id)
        streak = user.get('streak', 0)
        last_date_str = user.get('last_streak_date')
        high_streak = user.get('high_streak', 0)
        current_points = user.get('points', 0)
        
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date() if last_date_str else None
        
        if last_date == today:
            return streak, 0, current_points
        
        if last_date and (today - last_date).days == 1:
            streak += 1
        else:
            streak = 1
        
        base_reward = 0.5 + (streak - 1) * 0.1
        bonus = 0
        if streak == 6:
            bonus = 3
        elif streak == 15:
            bonus = 5
        elif streak == 30:
            bonus = 10
        
        total_reward = base_reward + bonus
        new_points = current_points + total_reward
        new_high_streak = max(high_streak, streak)
        
        await self.update_user(user_id, {
            'streak': streak,
            'last_streak_date': today_str,
            'high_streak': new_high_streak,
            'points': new_points
        })
        
        return streak, total_reward, new_points
    
    async def spend_points(self, user_id: int, cost: int) -> bool:
        user = await self.get_user(user_id)
        current_points = user.get('points', 0)
        
        if current_points >= cost:
            await self.update_user(user_id, {'points': current_points - cost})
            return True
        return False
    
    async def check_daily_key_claimed(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        claimed_at_str = user.get('daily_key_claimed_at')
        if not claimed_at_str:
            return False
        try:
            claimed_at = datetime.fromisoformat(claimed_at_str.replace('Z', '+00:00'))
            is_claimed = datetime.now(timezone.utc) - claimed_at < timedelta(hours=24)
            logging.info(f"Daily key check for {user_id}: claimed_at={claimed_at_str}, is_claimed={is_claimed}")
            return is_claimed
        except Exception as e:
            logging.error(f"Daily key check error for {user_id}: {e}")
            return False
    
    async def claim_daily_key(self, user_id: int):
        await self.update_user(user_id, {'daily_key_claimed_at': datetime.now(timezone.utc)})
    
    async def save_key(self, key: str, duration_days: int, user_id: int, user_name: str, is_daily: bool = False):
        """Save key to Firestore with panel-compatible format.
        - Daily keys: Expiry starts IMMEDIATELY when claimed (4 hours from now)
        - Regular keys: Expiry starts ONLY when device activated (HWID bind)
        """
        session = await self.get_session()
        doc_path = f"{FIREBASE_BASE_URL}/keys?key={FIREBASE_API_KEY}"
        
        stored_duration = 0 if is_daily else duration_days
        created_at = datetime.now(timezone.utc)
        
        # For daily keys, set expiry to 4 hours from NOW
        if is_daily:
            expiry_at = created_at + timedelta(hours=4)
            status = 'active'  # Daily keys are immediately active
        else:
            expiry_at = None
            status = 'unused'
        
        key_data = {
            'fields': {
                'key': {'stringValue': key},
                'duration': {'integerValue': str(stored_duration)},
                'status': {'stringValue': status},
                'reseller_uid': {'stringValue': str(user_id)},
                'reseller_name': {'stringValue': RESELLER_NAME},
                'is_trial': {'booleanValue': False},
                'is_daily': {'booleanValue': is_daily},
                'hwid': {'nullValue': None},
                'activated_at': {'timestampValue': created_at.isoformat() if is_daily else None} if is_daily else {'nullValue': None},
                'expiry_date': {'timestampValue': expiry_at.isoformat()} if is_daily else {'nullValue': None},
                'created_at': {'timestampValue': created_at.isoformat()},
                'sec_data': {'stringValue': '0x4f06288,0x4e9feb8,0x4dde3e0,0x4dfe838,0x2d911e0,0x3068c94,0x0294879d,0x02948795,0x029487a5'}
            }
        }
        async with session.post(doc_path, json=key_data) as resp:
            if resp.status != 200:
                logging.error(f"Save key failed: {await resp.text()}")
            else:
                # Increment user's total_keys counter
                await self.update_user(user_id, {'total_keys_increment': True})
    
    async def get_channel_member(self, user_id: int) -> dict:
        pass
    
    async def count_user_keys(self, user_id: int) -> int:
        """Count total keys generated by user (daily + purchased)"""
        session = await self.get_session()
        doc_path = f"{FIREBASE_BASE_URL}/keys?key={FIREBASE_API_KEY}"
        
        async with session.get(doc_path) as resp:
            if resp.status == 200:
                data = await resp.json()
                documents = data.get('documents', [])
                count = 0
                for doc in documents:
                    fields = doc.get('fields', {})
                    reseller_uid = fields.get('reseller_uid', {}).get('stringValue', '')
                    if str(reseller_uid) == str(user_id):
                        count += 1
                return count
            return 0

firebase_client = FirebaseClient()

async def count_user_keys(user_id: int) -> int:
    return await firebase_client.count_user_keys(user_id)

async def get_user(user_id: int, first_name: str = None, username: str = None):
    return await firebase_client.get_user(user_id, first_name, username)

async def update_user_points(user_id: int, points_change: float):
    await firebase_client.update_user_points(user_id, points_change)

async def update_streak(user_id: int):
    return await firebase_client.update_streak(user_id)

async def spend_points(user_id: int, cost: int) -> bool:
    return await firebase_client.spend_points(user_id, cost)

async def check_daily_key_claimed(user_id: int) -> bool:
    return await firebase_client.check_daily_key_claimed(user_id)

async def claim_daily_key(user_id: int):
    await firebase_client.claim_daily_key(user_id)

async def save_key(key: str, duration_days: int, user_id: int, user_name: str, is_daily: bool = False):
    await firebase_client.save_key(key, duration_days, user_id, user_name, is_daily)

def generate_key_string():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    segment = lambda: ''.join(random.choices(chars, k=5))
    return f"LIONX-{segment()}-{segment()}-{segment()}"

ADMIN_ID = 7107553688

class ReportState(StatesGroup):
    waiting_for_message = State()

class DailyKeyState(StatesGroup):
    waiting_for_confirm = State()

class AdminState(StatesGroup):
    waiting_broadcast = State()
    waiting_file_name = State()
    waiting_file_upload = State()
    waiting_report_reply = State()

KEY_COSTS = {
    "1day": 5,
    "3day": 8,
    "7day": 15,
    "15day": 25,
    "30day": 40
}

KEY_DURATIONS = {
    "1day": "1 Day",
    "3day": "3 Days",
    "7day": "7 Days",
    "15day": "15 Days",
    "30day": "30 Days"
}

async def check_channel_membership(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        status = member.status
        logging.info(f"Channel check for {user_id}: {status}")
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Channel check error for {user_id}: {e}")
        return False

def get_terms_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Accept & Continue", callback_data="accept_terms", style="success")]
    ])

def get_channel_join_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦁 Join Channel", url=CHANNEL_URL, style="success")],
        [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join", style="primary")]
    ])

def get_welcome_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦁 LionX Ofc", url=CHANNEL_URL, style="success")],
        [InlineKeyboardButton(text="✅ Verify", callback_data="verify", style="primary")]
    ])

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗝️ Daily Key", callback_data="daily_key", style="primary")],
        [InlineKeyboardButton(text="⚙️ Gen Key", callback_data="generate_key", style="success"),
         InlineKeyboardButton(text="⌛ Streak", callback_data="check_streak", style="success")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile", style="primary"),
         InlineKeyboardButton(text="📨 Invite", callback_data="invite", style="primary")],
        [InlineKeyboardButton(text="📝 Report", callback_data="report", style="danger"),
         InlineKeyboardButton(text="📜 Terms", callback_data="terms", style="danger")],
        [InlineKeyboardButton(text="📁 Download File", callback_data="download_file", style="success")]
    ])

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user = message.from_user
    user_id = user.id
    args = message.text.split()
    logging.info(f"/start from user {user_id} ({user.first_name}) args={args}")
    
    db_user = await get_user(user_id, user.first_name, user.username)
    
    # Handle invite tracking
    if len(args) > 1:
        invite_code = args[1]
        if invite_code.isdigit():
            inviter_id = int(invite_code)
            if inviter_id != user_id:
                # Check if already tracked
                inviter_db = await get_user(inviter_id)
                invited_list = inviter_db.get('invited_users', [])
                if user_id not in invited_list:
                    # Award point to inviter
                    await firebase_client.update_user(inviter_id, {
                        'points': inviter_db.get('points', 0) + 1,
                        'total_invites': inviter_db.get('total_invites', 0) + 1,
                        'invited_users': invited_list + [user_id]
                    })
                    
                    # Notify inviter
                    try:
                        await bot.send_message(
                            inviter_id,
                            f"🎉 <b>Successful Invite!</b>\n\n"
                            f"You have successfully invited <b>@{user.username or user.first_name}</b>\n"
                            f"✅ Earned <b>+1 point</b>\n\n"
                            f"🔥 Keep doing great!",
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_main", style="primary")]
                            ])
                        )
                    except:
                        pass  # User might have blocked bot
    
    # Check maintenance mode first
    global maintenance_mode
    if maintenance_mode and message.from_user.id != ADMIN_ID:
        maint_text = (
            f"<b>🔧 Maintenance Mode</b>\n\n"
            f"🦁 <b>LionX Server Currently Under Maintenance</b>\n\n"
            f"Please wait and try again later.\n\n"
            f"<i>We'll be back soon!</i>"
        )
        await message.answer_video(
                video=WELCOME_VIDEO,
                caption=maint_text,
        )
        return
    
    is_member = await check_channel_membership(user_id)
    
    if not is_member:
        join_text = (
            f"<b>🔒 Channel Required</b>\n\n"
            f"Welcome <i>{user.first_name or 'User'}!</i>\n\n"
            f"To use this bot, you must join our official channel:\n"
            f"🦁 <b>LionX Engine</b>\n\n"
            f"Click the button below to join, then press <b>\"I've Joined\"</b> to continue."
        )
        await message.answer_video(
            video=WELCOME_VIDEO,
            caption=join_text,
            reply_markup=get_channel_join_keyboard()
        )
        return
    
    await show_main_menu(message, user.first_name or "User")


@dp.message(Command("resetdaily"))
async def reset_daily_cmd(message: types.Message):
    """Admin command to reset user's daily key claim"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Access denied! Only admin can use this command.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Usage: /resetdaily <user_id>\nExample: /resetdaily 123456789")
        return
    
    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be a number.")
        return
    
    # Reset daily key claim
    await firebase_client.update_user(target_user_id, {'daily_key_claimed_at': None})
    
    # Notify admin
    await message.answer(f"✅ Daily key claim reset for user <code>{target_user_id}</code>!")
    
    # Notify user
    try:
        await bot.send_message(
            target_user_id,
            f"🔄 <b>Daily Key Reset</b>\n\n"
            f"Your daily key claim has been <b>reset by admin</b>.\n\n"
            f"✅ You can now claim your <b>free daily key</b> again!\n\n"
            f"🗝️ Go to <b>Daily Key</b> and click <b>Confirm</b> to generate a new 4-hour key.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗝️ Claim Daily Key", callback_data="daily_key", style="primary")]
            ])
        )
    except:
        pass  # User might have blocked bot


@dp.message(Command("admin"))
async def admin_panel_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Access denied!")
        return
    
    panel_text = (
        f"<b>🔐 Admin Control Panel</b>\n\n"
        f"Welcome <b>Khalid Khan</b>\n\n"
        f"Select an option below:"
    )
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast", style="primary")],
        [InlineKeyboardButton(text="📁 Add File", callback_data="admin_add_file", style="success")],
        [InlineKeyboardButton(text="📋 List Files", callback_data="admin_list_files", style="primary")],
        [InlineKeyboardButton(text="👥 User Stats", callback_data="admin_user_stats", style="primary")],
        [InlineKeyboardButton(text="🔧 Maintenance Mode", callback_data="admin_maintenance", style="danger")],
        [InlineKeyboardButton(text="🔄 Reset All Daily Keys", callback_data="admin_reset_all_daily", style="danger")],
        [InlineKeyboardButton(text="🔙 Close", callback_data="admin_close", style="danger")]
    ])
    
    await message.answer_video(
        video=MAIN_MENU_VIDEO,
        caption=panel_text,
        reply_markup=admin_keyboard
    )

@dp.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    await callback.message.delete()
    await callback.answer()

@dp.callback_query(F.data == "admin_maintenance")
async def admin_maintenance_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    global maintenance_mode
    maintenance_mode = not maintenance_mode
    
    status = "ON 🔴" if maintenance_mode else "OFF 🟢"
    await callback.answer(f"Maintenance Mode: {status}", show_alert=True)
    
    # Refresh panel
    panel_text = (
        f"<b>🔐 Admin Control Panel</b>\n\n"
        f"Welcome <b>Khalid Khan</b>\n\n"
        f"Select an option below:"
    )
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast", style="primary")],
        [InlineKeyboardButton(text="📁 Add File", callback_data="admin_add_file", style="success")],
        [InlineKeyboardButton(text="📋 List Files", callback_data="admin_list_files", style="primary")],
        [InlineKeyboardButton(text="👥 User Stats", callback_data="admin_user_stats", style="primary")],
        [InlineKeyboardButton(text="🔧 Maintenance Mode", callback_data="admin_maintenance", style="danger")],
        [InlineKeyboardButton(text="🔄 Reset All Daily Keys", callback_data="admin_reset_all_daily", style="danger")],
        [InlineKeyboardButton(text="🔙 Close", callback_data="admin_close", style="danger")]
    ])
    
    try:
        await callback.message.edit_caption(
            caption=panel_text,
            reply_markup=admin_keyboard
        )
    except:
        pass

@dp.callback_query(F.data == "admin_reset_all_daily")
async def admin_reset_all_daily_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    await callback.answer("🔄 Resetting daily keys for all users...", show_alert=True)
    
    # Get all users and reset their daily_key_claimed_at
    session = await firebase_client.get_session()
    doc_path = f"{FIREBASE_BASE_URL}/users?key={FIREBASE_API_KEY}"
    
    async with session.get(doc_path) as resp:
        if resp.status == 200:
            data = await resp.json()
            users = data.get('documents', [])
            
            count = 0
            for user_doc in users:
                fields = user_doc.get('fields', {})
                user_id = int(fields.get('user_id', {}).get('integerValue', '0'))
                if user_id:
                    await firebase_client.update_user(user_id, {'daily_key_claimed_at': None})
                    count += 1
            
            await callback.answer(f"✅ Reset daily keys for {count} users!", show_alert=True)
        else:
            await callback.answer("❌ Failed to fetch users!", show_alert=True)

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    await state.set_state(AdminState.waiting_broadcast)
    await callback.message.edit_caption(
        caption=(
            f"<b>📢 Broadcast Message</b>\n\n"
            f"Send the message you want to broadcast to all users.\n"
            f"Supports HTML formatting.\n\n"
            f"<i>Type /cancel to cancel</i>"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Panel", callback_data="admin_back", style="primary")]
        ])
    )
    await callback.answer()

@dp.message(AdminState.waiting_broadcast)
async def admin_broadcast_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Broadcast cancelled.")
        return
    
    # Get all user IDs
    session = await firebase_client.get_session()
    doc_path = f"{FIREBASE_BASE_URL}/users?key={FIREBASE_API_KEY}"
    
    async with session.get(doc_path) as resp:
        if resp.status == 200:
            data = await resp.json()
            users = data.get('documents', [])
            
            sent = 0
            failed = 0
            for user_doc in users:
                try:
                    user_data = user_doc.get('fields', {})
                    user_id = int(user_data.get('user_id', {}).get('integerValue', '0'))
                    if user_id:
                        await bot.send_message(user_id, message.html_text)
                        sent += 1
                except:
                    failed += 1
            
            await message.answer(
                f"✅ Broadcast Complete!\n\n"
                f"✅ Sent: {sent}\n"
                f"❌ Failed: {failed}"
            )
    
    await state.clear()

@dp.callback_query(F.data == "admin_add_file")
async def admin_add_file_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    await state.set_state(AdminState.waiting_file_name)
    await callback.message.edit_caption(
        caption=(
            f"<b>📁 Add New File</b>\n\n"
            f"Enter the file name/title (e.g., <b>LionX v1</b>):\n\n"
            f"<i>Type /cancel to cancel</i>"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Panel", callback_data="admin_back", style="primary")]
        ])
    )
    await callback.answer()

@dp.message(AdminState.waiting_file_name)
async def admin_file_name_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ File upload cancelled.")
        return
    
    file_name = message.text.strip()
    await state.update_data(file_name=file_name)
    await state.set_state(AdminState.waiting_file_upload)
    
    await message.answer(
        f"✅ File name: <b>{file_name}</b>\n\n"
        f"Now send the file (document) you want to upload.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Panel", callback_data="admin_back", style="primary")]
        ])
    )

@dp.message(AdminState.waiting_file_upload)
async def admin_file_upload_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ File upload cancelled.")
        return
    
    # Expect a MediaFire link
    mediafire_link = message.text.strip()
    if not mediafire_link.startswith("http"):
        await message.answer("❌ Please send a valid MediaFire link (starting with http/https)")
        return
    
    data = await state.get_data()
    file_name = data.get('file_name', 'Unknown')
    
    # Save file info to Firestore with MediaFire link
    session = await firebase_client.get_session()
    doc_path = f"{FIREBASE_BASE_URL}/bot_files?key={FIREBASE_API_KEY}"
    
    file_data = {
        'fields': {
            'title': {'stringValue': file_name},
            'mediafire_link': {'stringValue': mediafire_link},
            'uploaded_by': {'stringValue': str(message.from_user.id)},
            'uploaded_at': {'timestampValue': datetime.now(timezone.utc).isoformat()}
        }
    }
    
    async with session.post(doc_path, json=file_data) as resp:
        resp_text = await resp.text()
        if resp.status in (200, 201):
            await message.answer(
                f"✅ File link saved successfully!\n\n"
                f"📁 <b>Title:</b> {file_name}\n"
                f"🔗 <b>MediaFire Link:</b> {mediafire_link}"
            )
        else:
            await message.answer(f"❌ Failed to save file info: {resp_text}")
            logging.error(f"File save failed: {resp.status} - {resp_text}")
    
    await state.clear()

@dp.callback_query(F.data == "admin_list_files")
async def admin_list_files_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    await callback.answer("📋 Loading files...")
    
    session = await firebase_client.get_session()
    doc_path = f"{FIREBASE_BASE_URL}/bot_files?key={FIREBASE_API_KEY}"
    
    async with session.get(doc_path) as resp:
        if resp.status == 200:
            data = await resp.json()
            files = data.get('documents', [])
            
            if not files:
                text = "📁 No files uploaded yet."
            else:
                text = f"<b>📁 Uploaded Files ({len(files)})</b>\n\n"
                for i, doc in enumerate(files[:10], 1):
                    fields = doc.get('fields', {})
                    title = fields.get('title', {}).get('stringValue', 'Unknown')
                    orig = fields.get('original_name', {}).get('stringValue', 'Unknown')
                    text += f"{i}. <b>{title}</b> ({orig})\n"
        
            await callback.message.edit_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back to Panel", callback_data="admin_back", style="primary")]
                ])
            )
        else:
            await callback.answer("❌ Failed to fetch files!", show_alert=True)
    
    await callback.answer()

@dp.callback_query(F.data == "admin_user_stats")
async def admin_user_stats_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    await callback.answer("👥 Loading stats...")
    
    session = await firebase_client.get_session()
    doc_path = f"{FIREBASE_BASE_URL}/users?key={FIREBASE_API_KEY}"
    
    async with session.get(doc_path) as resp:
        if resp.status == 200:
            data = await resp.json()
            users = data.get('documents', [])
            
            total = len(users)
            total_points = 0
            total_keys = 0
            for user_doc in users:
                fields = user_doc.get('fields', {})
                total_points += fields.get('points', {}).get('doubleValue', 0)
            
            text = (
                f"<b>👥 User Statistics</b>\n\n"
                f"👤 Total Users: <b>{total}</b>\n"
                f"⭐ Total Points: <b>{total_points:.1f}</b>\n"
            )
            
            await callback.message.edit_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back to Panel", callback_data="admin_back", style="primary")]
                ])
            )
        else:
            await callback.answer("❌ Failed to fetch stats!", show_alert=True)
    
    await callback.answer()

@dp.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    await state.clear()
    
    panel_text = (
        f"<b>🔐 Admin Control Panel</b>\n\n"
        f"Welcome <b>Khalid Khan</b>\n\n"
        f"Select an option below:"
    )
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast", style="primary")],
        [InlineKeyboardButton(text="📁 Add File", callback_data="admin_add_file", style="success")],
        [InlineKeyboardButton(text="📋 List Files", callback_data="admin_list_files", style="primary")],
        [InlineKeyboardButton(text="👥 User Stats", callback_data="admin_user_stats", style="primary")],
        [InlineKeyboardButton(text="🔧 Maintenance Mode", callback_data="admin_maintenance", style="danger")],
        [InlineKeyboardButton(text="🔄 Reset All Daily Keys", callback_data="admin_reset_all_daily", style="danger")],
        [InlineKeyboardButton(text="🔙 Close", callback_data="admin_close", style="danger")]
    ])
    
    await callback.message.edit_caption(
        caption=panel_text,
        reply_markup=admin_keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "check_join")
async def check_join_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_member = await check_channel_membership(user_id)
    
    if is_member:
        # Check if user has accepted terms (we can use a flag)
        db_user = await get_user(user_id)
        terms_accepted = db_user.get('terms_accepted', False)
        
        await callback.message.delete()
        
        if not terms_accepted:
            # Show terms first
            terms_text = (
                f"<b>📜 Terms of Service</b>\n\n"
                f"🔐 <b>Key Usage Policy</b>\n"
                f"• Keys generated by this bot are for <b>personal use only</b>\n"
                f"• <b>Selling, trading, or sharing keys is strictly prohibited</b>\n"
                f"• Each key binds to <b>one device (HWID)</b> and cannot be transferred\n\n"
                f"⚖️ <b>Violation Consequences</b>\n"
                f"• <b>Permanent ban</b> from LionX community\n"
                f"• <b>Public exposure</b> on main channel as <b>SCAMMER</b>\n"
                f"• <b>Device blacklist</b> - no future keys will work\n\n"
                f"⚠️ <b>Disclaimer</b>\n"
                f"• Use of LionX bot is <b>at your own risk</b>\n"
                f"• We are <b>not responsible</b> for any bans, losses, or damages\n"
                f"• No refunds or compensation for any reason\n\n"
                f"🤝 By using this bot, you <b>agree</b> to all terms above.\n"
                f"<i>Violations will be dealt with zero tolerance.</i>"
            )
            await callback.message.answer_video(
                video=WELCOME_VIDEO,
                caption=terms_text,
                reply_markup=get_terms_keyboard()
            )
        else:
            await show_main_menu(callback, callback.from_user.first_name or "User")
            await callback.answer("Welcome!")
    else:
        await callback.answer("❌ You haven't joined the channel yet!", show_alert=True)

@dp.callback_query(F.data == "verify")
async def verify_callback(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("Join channel first!", show_alert=True)
        return
    
    terms_text = (
        f"<b>📜 Terms of Service</b>\n\n"
        f"🔐 <b>Key Usage Policy</b>\n"
        f"• Keys generated by this bot are for <b>personal use only</b>\n"
        f"• <b>Selling, trading, or sharing keys is strictly prohibited</b>\n"
        f"• Each key binds to <b>one device (HWID)</b> and cannot be transferred\n\n"
        f"⚖️ <b>Violation Consequences</b>\n"
        f"• <b>Permanent ban</b> from LionX community\n"
        f"• <b>Public exposure</b> on main channel as <b>SCAMMER</b>\n"
        f"• <b>Device blacklist</b> - no future keys will work\n\n"
        f"⚠️ <b>Disclaimer</b>\n"
        f"• Use of LionX bot is <b>at your own risk</b>\n"
        f"• We are <b>not responsible</b> for any bans, losses, or damages\n"
        f"• No refunds or compensation for any reason\n\n"
        f"🤝 By using this bot, you <b>agree</b> to all terms above.\n"
        f"<i>Violations will be dealt with zero tolerance.</i>"
    )
    await callback.message.delete()
    await callback.message.answer_video(
        video=WELCOME_VIDEO,
        caption=terms_text,
        reply_markup=get_terms_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "accept_terms")
async def accept_terms_callback(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("🔒 Join channel first!", show_alert=True)
        return
    
    # Mark terms as accepted
    await firebase_client.update_user(user_id, {'terms_accepted': True})
    
    await show_main_menu(callback, user.first_name or "User")
    await callback.answer("✅ Welcome to LionX!")

@dp.callback_query(F.data == "check_streak")
async def check_streak_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    streak, reward, new_points = await update_streak(user_id)
    
    if reward == 0:
        await callback.answer(f"⌛ Already claimed today! Streak: {streak} days", show_alert=True)
    else:
        bonus_text = ""
        if streak == 6:
            bonus_text = "\n🎁 <b>6-day bonus: +3 points!</b>"
        elif streak == 15:
            bonus_text = "\n🎁 <b>15-day bonus: +5 points!</b>"
        elif streak == 30:
            bonus_text = "\n🎁 <b>30-day bonus: +10 points!</b>"
        
        await callback.message.edit_caption(
            caption=(
                f"<b>⌛ Daily Streak Claimed!</b>\n\n"
                f"🔥 <b>Streak:</b> {streak} days\n"
                f"⭐ <b>Earned:</b> +{reward:.1f} points{bonus_text}\n"
                f"💰 <b>Total Points:</b> {new_points:.1f}"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data="back_main", style="primary")]
            ])
        )
        await callback.answer(f"✅ Claimed +{reward:.1f} points!")

@dp.callback_query(F.data == "daily_key")
async def daily_key_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("🔒 Join channel first!", show_alert=True)
        return
    
    already_claimed = await check_daily_key_claimed(user_id)
    
    if already_claimed:
        # Get the claim time to show when next claim available
        db_user = await get_user(user_id)
        claimed_at_str = db_user.get('daily_key_claimed_at')
        
        next_claim_text = "Wait 24 hours"
        if claimed_at_str:
            try:
                claimed_at = datetime.fromisoformat(claimed_at_str.replace('Z', '+00:00'))
                next_claim = claimed_at + timedelta(hours=24)
                remaining = next_claim - datetime.now(timezone.utc)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                if hours > 0:
                    next_claim_text = f"{hours}h {minutes}m remaining"
                else:
                    next_claim_text = f"{minutes}m remaining"
            except:
                pass
        
        # Get the key from DB (we need to query the keys collection)
        # For now, show claimed state
        claimed_text = (
            f"<b>⌛ Daily Key Already Claimed</b>\n\n"
            f"✅ <b>Status:</b> Already claimed today\n"
            f"⏰ <b>Next claim:</b> {next_claim_text}\n\n"
            f"🔄 Come back tomorrow for your free 4-hour key!"
        )
        await send_menu_photo(callback, claimed_text, InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back", callback_data="back_main", style="primary")]
        ]))
        return
    
    await state.set_state(DailyKeyState.waiting_for_confirm)
    daily_key_text = (
        f"<b>🗝️ Claim Your Free Daily Key</b>\n\n"
        f"⚠️ <b>Note:</b> The 4-hour timer starts <b>IMMEDIATELY</b> when you confirm.\n\n"
        f"⏰ <b>Expire Time:</b> <code>4 Hours from activation</code>\n\n"
        f"👇 Please click the <b>Confirm</b> button to activate your key."
    )
    await send_menu_photo(callback, daily_key_text, get_daily_key_confirm_keyboard())

@dp.callback_query(F.data == "confirm_daily_key", DailyKeyState.waiting_for_confirm)
async def confirm_daily_key_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("🔒 Join channel first!", show_alert=True)
        return
    
    already_claimed = await check_daily_key_claimed(user_id)
    if already_claimed:
        await callback.answer("⌛ Already claimed!", show_alert=True)
        return
    
    # Generate 4-hour key with proper panel format: LIONX-XXXXX-XXXXX-XXXXX
    key = generate_key_string()
    
    # Save to Firestore with is_daily=True - expiry starts NOW
    await save_key(key, 0, user_id, callback.from_user.first_name or "User", is_daily=True)
    await claim_daily_key(user_id)
    
    done_text = (
        f"<b>✅ Daily Key Activated!</b>\n\n"
        f"<b>You have activated your 4 hours key</b>\n\n"
        f"🗝️ <b>Your Key:</b>\n<code>{key}</code>\n\n"
        f"⏰ <b>Expire Time:</b> <code>4 Hours from NOW</code>\n\n"
        f"🔔 You will get notified once your key expires.\n\n"
        f"🦁 <b>Enjoy LionX!</b>"
    )
    await send_menu_photo(callback, done_text, get_daily_key_done_keyboard(key))

@dp.callback_query(F.data == "cancel_daily_key", DailyKeyState.waiting_for_confirm)
async def cancel_daily_key_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback, callback.from_user.first_name or "User")

def get_daily_key_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_daily_key", style="success"),
         InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_daily_key", style="danger")]
    ])

def get_daily_key_done_keyboard(key: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Copy Key", copy_text=CopyTextButton(text=key), style="success"),
         InlineKeyboardButton(text="🔙 Back", callback_data="back_main", style="primary")]
    ])

@dp.callback_query(F.data == "generate_key")
async def generate_key_callback(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("Join channel first!", show_alert=True)
        return
    
    db_user = await get_user(user_id, user.first_name, user.username)
    points = db_user.get('points', 0)
    
    gen_key_text = (
        f"<b>⚙️ Generate Key</b>\n\n"
        f"⚠️ <b>Note:</b> Each key can be used only on one device, bind to your device <b>HWID</b>.\n\n"
        f"⭐ <b>Your Points:</b> <code>{points:.1f}</code>\n\n"
        f"💰 <b>Key Prices:</b>\n"
        f"• 1 Day: 5 points\n"
        f"• 3 Days: 8 points\n"
        f"• 7 Days: 15 points\n"
        f"• 15 Days: 25 points\n"
        f"• 30 Days: 40 points"
    )
    await send_menu_photo(callback, gen_key_text, get_gen_key_keyboard())

@dp.callback_query(F.data.startswith("gen_"))
async def gen_key_duration_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    duration_key = callback.data.split("_")[1]
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("Join channel first!", show_alert=True)
        return
    
    if duration_key not in KEY_COSTS:
        await callback.answer("Invalid key duration!", show_alert=True)
        return
    
    cost = KEY_COSTS[duration_key]
    duration_name = KEY_DURATIONS[duration_key]
    duration_days = int(duration_name.split()[0])
    
    success = await spend_points(user_id, cost)
    if not success:
        await callback.answer(f"Not enough points! Need {cost} points.", show_alert=True)
        return
    
    key = generate_key_string()
    await save_key(key, duration_days, user_id, callback.from_user.first_name or "User", is_daily=False)
    
    db_user = await get_user(user_id)
    new_points = db_user.get('points', 0)
    
    await callback.message.edit_caption(
        caption=(
            f"<b>✅ Key Generated!</b>\n\n"
            f"🔑 <b>Duration:</b> {duration_name}\n"
            f"🔐 <b>Key:</b> <code>{key}</code>\n"
            f"💰 <b>Cost:</b> {cost} points\n"
            f"⭐ <b>Remaining Points:</b> {new_points:.1f}\n\n"
            f"⚠️ <b>Note:</b> This key binds to one device (HWID).\n"
            f"💾 <b>Saved to panel database!</b>\n"
            f"⏰ <b>Expiry starts on device activation (HWID bind)</b>"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Copy Key", copy_text=CopyTextButton(text=key), style="success"),
             InlineKeyboardButton(text="🔙 Back", callback_data="generate_key", style="primary")]
        ])
    )
    await callback.answer(f"✅ {duration_name} key generated for {cost} points!")

def get_gen_key_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Day", callback_data="gen_1day", style="primary"),
         InlineKeyboardButton(text="3 Days", callback_data="gen_3day", style="primary")],
        [InlineKeyboardButton(text="7 Days", callback_data="gen_7day", style="primary"),
         InlineKeyboardButton(text="15 Days", callback_data="gen_15day", style="primary")],
        [InlineKeyboardButton(text="30 Days", callback_data="gen_30day", style="success")],
        [InlineKeyboardButton(text="Back", callback_data="back_main", style="primary")]
    ])

@dp.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("Join channel first!", show_alert=True)
        return
    
    db_user = await get_user(user_id, user.first_name, user.username)
    first_name = db_user.get('first_name', 'N/A')
    username = f"@{db_user['username']}" if db_user.get('username') else "N/A"
    total_invites = db_user.get('total_invites', 0)
    high_streak = db_user.get('high_streak', 0)
    member_since = db_user.get('member_since', 'Unknown')
    points = db_user.get('points', 0)
    streak = db_user.get('streak', 0)
    
    profile_text = (
        f"<b>👤 Profile</b>\n\n"
        f"👤 <b>Name:</b> <i>{first_name}</i>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"📨 <b>Total Invites:</b> <code>{total_invites}</code>\n"
        f"⌛ <b>High Streak:</b> <code>{high_streak}</code> days\n"
        f"📅 <b>Member Since:</b> <code>{member_since}</code>\n"
        f"⭐ <b>Points:</b> <code>{points:.1f}</code>\n"
        f"🔥 <b>Current Streak:</b> <code>{streak}</code> days"
    )
    await send_menu_photo(callback, profile_text, get_profile_keyboard())

def get_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data="back_main", style="primary")]
    ])

@dp.callback_query(F.data == "report")
async def report_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ReportState.waiting_for_message)
    report_text = (
        f"<b>📝 Report / Support</b>\n\n"
        f"If you are facing any issue, you can write directly in bot.\n"
        f"<b>Admin will answer you shortly.</b>\n\n"
        f"<i>Type your message below...</i>"
    )
    await send_menu_photo(callback, report_text, get_report_keyboard())

@dp.message(ReportState.waiting_for_message)
async def report_message_handler(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Save report to Firestore using message_id as document ID
    session = await firebase_client.get_session()
    doc_path = f"{FIREBASE_BASE_URL}/reports/{message.message_id}?key={FIREBASE_API_KEY}"
    
    report_data = {
        'fields': {
            'user_id': {'integerValue': str(message.from_user.id)},
            'username': {'stringValue': message.from_user.username or "N/A"},
            'first_name': {'stringValue': message.from_user.first_name or "User"},
            'message': {'stringValue': message.text},
            'status': {'stringValue': 'pending'},
            'created_at': {'timestampValue': datetime.now(timezone.utc).isoformat()},
            'admin_reply': {'nullValue': None}
        }
    }
    
    async with session.patch(doc_path, json=report_data) as resp:
        if resp.status in (200, 201):
            # Notify admin
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"📝 <b>New Report Received</b>\n\n"
                    f"👤 <b>From:</b> {message.from_user.first_name} (@{message.from_user.username or 'N/A'})\n"
                    f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n\n"
                    f"📝 <b>Message:</b>\n{message.text}\n\n"
                    f"🆔 <b>Report ID:</b> <code>{message.message_id}</code>",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="💬 Reply", callback_data=f"reply_report_{message.message_id}", style="primary")]
                    ])
                )
            except:
                pass
            
            await message.answer(
                f"<b>✅ Message Sent!</b>\n\n"
                f"Admin will review your message and answer you.",
                reply_markup=get_report_done_keyboard()
            )
        else:
            await message.answer("❌ Failed to send report. Please try again.")

@dp.callback_query(F.data.startswith("reply_report_"))
async def admin_reply_report_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    report_id = callback.data.split("_")[2]
    await state.set_state(AdminState.waiting_report_reply)
    await state.update_data(report_id=report_id)
    
    try:
        await callback.message.edit_text(
            text=(
                f"<b>💬 Reply to Report</b>\n\n"
                f"Write your reply below. It will be sent to the user directly.\n\n"
                f"<i>Type /cancel to cancel</i>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data="admin_back", style="primary")]
            ])
        )
    except:
        await callback.message.edit_caption(
            caption=(
                f"<b>💬 Reply to Report</b>\n\n"
                f"Write your reply below. It will be sent to the user directly.\n\n"
                f"<i>Type /cancel to cancel</i>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data="admin_back", style="primary")]
            ])
        )
    await callback.answer()

@dp.message(AdminState.waiting_report_reply)
async def admin_report_reply_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Reply cancelled.")
        return
    
    data = await state.get_data()
    report_id = data.get('report_id')
    
    # Find the report to get user_id
    session = await firebase_client.get_session()
    doc_path = f"{FIREBASE_BASE_URL}/reports/{report_id}?key={FIREBASE_API_KEY}"
    
    async with session.get(doc_path) as resp:
        if resp.status == 200:
            data = await resp.json()
            fields = data.get('fields', {})
            user_id = int(fields.get('user_id', {}).get('integerValue', '0'))
            
            if user_id:
                # Send reply to user
                try:
                    await bot.send_message(
                        user_id,
                        f"💬 <b>Admin Reply</b>\n\n"
                        f"{message.html_text}\n\n"
                        f"<i>— Admin</i>",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_main", style="primary")]
                        ])
                    )
                    
                    # Update report with reply
                    update_path = f"{FIREBASE_BASE_URL}/reports/{report_id}?key={FIREBASE_API_KEY}"
                    update_data = {
                        'fields': {
                            'status': {'stringValue': 'replied'},
                            'admin_reply': {'stringValue': message.text},
                            'replied_at': {'timestampValue': datetime.now(timezone.utc).isoformat()}
                        }
                    }
                    async with session.patch(f"{update_path}&updateMask.fieldPaths=status&updateMask.fieldPaths=admin_reply&updateMask.fieldPaths=replied_at", json=update_data) as resp:
                        pass
                    
                    await message.answer("✅ Reply sent to user!")
                except Exception as e:
                    await message.answer(f"❌ Failed to send reply: {e}")
            else:
                await message.answer("❌ User not found or already deleted.")
    
    await state.clear()

def get_report_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data="back_main", style="primary")]
    ])

def get_report_done_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back to Main Menu", callback_data="back_main", style="primary")]
    ])

@dp.callback_query(F.data == "terms")
async def terms_callback(callback: types.CallbackQuery):
    terms_text = (
        f"<b>📜 Terms of Service</b>\n\n"
        f"🔐 <b>Key Usage Policy</b>\n"
        f"• Keys generated by this bot are for <b>personal use only</b>\n"
        f"• <b>Selling, trading, or sharing keys is strictly prohibited</b>\n"
        f"• Each key binds to <b>one device (HWID)</b> and cannot be transferred\n\n"
        f"⚖️ <b>Violation Consequences</b>\n"
        f"• <b>Permanent ban</b> from LionX community\n"
        f"• <b>Public exposure</b> on main channel as <b>SCAMMER</b>\n"
        f"• <b>Device blacklist</b> - no future keys will work\n\n"
        f"⚠️ <b>Disclaimer</b>\n"
        f"• Use of LionX bot is <b>at your own risk</b>\n"
        f"• We are <b>not responsible</b> for any bans, losses, or damages\n"
        f"• No refunds or compensation for any reason\n\n"
        f"🤝 By using this bot, you <b>agree</b> to all terms above.\n"
        f"<i>Violations will be dealt with zero tolerance.</i>"
    )
    await send_menu_photo(callback, terms_text, get_terms_keyboard())

def get_terms_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Accept & Continue", callback_data="accept_terms", style="success")]
    ])

@dp.callback_query(F.data == "invite")
async def invite_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        await callback.answer("Join channel first!", show_alert=True)
        return
    
    db_user = await get_user(user_id, callback.from_user.first_name, callback.from_user.username)
    invite_link = f"https://t.me/LionXsupport_bot?start={user_id}"
    invite_text = (
        f"<b>📨 Invite Friends</b>\n\n"
        f"🔗 Share your invite link below. Each friend you invite gives you <b>1 point</b>!\n\n"
        f"👥 <b>Total Invites:</b> <code>{db_user.get('total_invites', 0)}</code>\n"
        f"⭐ <b>Points from Invites:</b> <code>{db_user.get('total_invites', 0)}</code>\n\n"
        f"🔗 <b>Your Invite Link:</b>\n"
        f"<code>{invite_link}</code>\n\n"
        f"📤 Press <b>Share</b> to send to friends"
    )
    await send_menu_photo(callback, invite_text, get_invite_keyboard())

def get_invite_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main", style="primary"),
         InlineKeyboardButton(text="📤 Share", switch_inline_query="", style="success")]
    ])

@dp.callback_query(F.data == "download_file")
async def download_file_callback(callback: types.CallbackQuery):
    is_member = await check_channel_membership(callback.from_user.id)
    if not is_member:
        await callback.answer("🔒 Join channel first!", show_alert=True)
        return
    
    await callback.answer()
    
    text = (
        f"<b>📁 Download File</b>\n\n"
        f"<b>LionX Beta v1.0.1</b>\n\n"
        f"Click below to download:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Media Fire", url="https://www.mediafire.com/file/jhlaz2zmn5o3hvl/LionX_Beta+V1.0.2.apk/file", style="success")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="back_main", style="danger")]
    ])
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "back_main")
async def back_main_callback(callback: types.CallbackQuery):
    user = callback.from_user
    await show_main_menu(callback, user.first_name or "User")

async def show_main_menu(message_or_callback, first_name: str):
    """Show main menu with user stats"""
    user_id = message_or_callback.from_user.id
    
    is_member = await check_channel_membership(user_id)
    if not is_member:
        # Show channel join requirement
        join_text = (
            f"<b>🔒 Channel Required</b>\n\n"
            f"Welcome <i>{first_name}!</i>\n\n"
            f"To use this bot, you must join our official channel:\n"
            f"🦁 <b>LionX Engine</b>\n\n"
            f"Click the button below to join, then press <b>\"I've Joined\"</b> to continue."
        )
        if hasattr(message_or_callback, 'message'):
            await message_or_callback.message.delete()
            await message_or_callback.message.answer_video(
                video=WELCOME_VIDEO,
                caption=join_text,
                reply_markup=get_channel_join_keyboard()
            )
        else:
            await message_or_callback.answer_video(
                video=WELCOME_VIDEO,
                caption=join_text,
                reply_markup=get_channel_join_keyboard()
            )
        return
    
    db_user = await get_user(user_id, first_name)
    points = db_user.get('points', 0)
    invites = db_user.get('total_invites', 0)
    streak = db_user.get('streak', 0)
    generated_keys = db_user.get('total_keys', 0)
    username = db_user.get('username', '')
    
    # Username link
    username_text = f"@{username}" if username else "N/A"
    
    main_menu_text = (
        f"<b>Hi <i>{first_name}</i></b>\n"
        f"🔗 <b>Username:</b> <a href='https://t.me/{username}'>{username_text}</a>\n\n"
        f"⭐ <b>Points:</b> <code>{points:.1f}</code>\n"
        f"👥 <b>Invites:</b> <code>{invites}</code>\n"
        f"⌛ <b>Streak:</b> <code>{streak}</code> days\n"
        f"🔑 <b>Generated Keys:</b> <code>{generated_keys}</code>"
    )
    
    if hasattr(message_or_callback, 'message'):
        # It's a callback query
        try:
            await message_or_callback.message.delete()
        except:
            pass
        await message_or_callback.message.answer_video(
            video=MAIN_MENU_VIDEO,
            caption=main_menu_text,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # It's a message
        await message_or_callback.answer_video(
            video=MAIN_MENU_VIDEO,
            caption=main_menu_text,
            reply_markup=get_main_menu_keyboard()
        )

async def send_menu_photo(callback: types.CallbackQuery, caption: str, keyboard):
    try:
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=keyboard
        )
    except:
        await callback.message.delete()
        await callback.message.answer_video(
            video=MAIN_MENU_VIDEO,
            caption=caption,
            reply_markup=keyboard
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())