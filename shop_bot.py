import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telegram.error import TelegramError
import datetime

TOKEN = "7865119203:AAG7BNEEc97UKqIalG3z1K9sEqdDKyOQh9Y"

logging.basicConfig(level=logging.INFO)

PRODUCTS = [
    # Prime
    {"name": "Prime 1 Month", "price": 99},
    {"name": "Prime 6 Months", "price": 299},
    # Other
    {"name": "Other 1 Month", "price": 99},
    {"name": "Other 3 Months", "price": 199},
    {"name": "Other 6 Months", "price": 299},
    # Canva Premium
    {"name": "Canva Premium 1 Month", "price": 99},
    {"name": "Canva Premium 6 Months", "price": 299},
    # Tidal Music
    {"name": "Tidal Music 1 Month", "price": 99},
    {"name": "Tidal Music 6 Months", "price": 299},
    # Proton
    {"name": "Proton 1 Month", "price": 99},
    {"name": "Proton 6 Months", "price": 299},
    # Surfshark
    {"name": "Surfshark 1 Month", "price": 99},
    {"name": "Surfshark 6 Months", "price": 299},
    # Temp Number
    {"name": "Temp Number 1 Month", "price": 99},
    {"name": "Temp Number 6 Months", "price": 299},
    # Mod.APK
    {"name": "Mod.APK 1 Month", "price": 99},
    {"name": "Mod.APK 6 Months", "price": 299},
    # MS365
    {"name": "MS365 1 Month", "price": 99},
    {"name": "MS365 6 Months", "price": 299},
]

CART = {}

SELECTING, ADDING = range(2)

# After you get the correct chat ID, update this value:
GROUP_CHAT_ID = -1003132052445  # Updated group chat ID

OWNER_ID = 7108572857
ADMIN_IDS = {OWNER_ID}  # Add more admin IDs here if needed

# Store purchases and users
PURCHASE_HISTORY = []
USERS = set()
ADMIN_CHAT = set()
BANNED_USERS = set()

BOT_ACTIVE = True  # Controls if bot responds to users

def get_product_keyboard():
    return ReplyKeyboardMarkup([[p["name"]] for p in PRODUCTS] + [["View Cart", "Checkout"]], one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    user_id = update.effective_user.id
    if user_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END
    if not BOT_ACTIVE and not is_admin(user_id):
        return ConversationHandler.END
    USERS.add(user_id)
    CART[user_id] = []
    await update.message.reply_text(
        "Welcome to the Shop Bot! What would you like to buy?",
        reply_markup=get_product_keyboard()
    )
    # Notify group of new user
    user = update.effective_user
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=f"👤 New user started the bot:\nName: {user.full_name}\nUsername: @{user.username if user.username else 'N/A'}\nUser ID: {user_id}"
    )
    return SELECTING

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    try:
        raise context.error
    except Exception as e:
        if update and hasattr(update, "message") and update.message:
            await update.message.reply_text(f"An error occurred: {e}")

ABUSE_WORDS = {"fuck", "shit", "bitch", "abuse", "mc", "bc", "chutiya", "madarchod", "bhenchod"}  # Add more as needed
SPAM_LIMIT = 5  # messages in a short time
SPAM_WINDOW = 10  # seconds

from collections import defaultdict, deque
import time

USER_MESSAGE_TIMES = defaultdict(lambda: deque(maxlen=SPAM_LIMIT))

async def check_abuse_and_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.lower() if update.message.text else ""
    # Abuse detection
    if any(word in text for word in ABUSE_WORDS):
        BANNED_USERS.add(user_id)
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
        except Exception:
            pass
        await update.message.reply_text("You have been banned for abusive language.")
        return True
    # Spam detection
    now = time.time()
    USER_MESSAGE_TIMES[user_id].append(now)
    times = USER_MESSAGE_TIMES[user_id]
    if len(times) == SPAM_LIMIT and (now - times[0]) < SPAM_WINDOW:
        BANNED_USERS.add(user_id)
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
        except Exception:
            pass
        await update.message.reply_text("You have been banned for spamming.")
        return True
    return False

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    user_id = update.effective_user.id
    if not BOT_ACTIVE and not is_admin(user_id):
        return
    # Abuse/spam check
    if await check_abuse_and_spam(update, context):
        return
    text = update.message.text
    if text == "View Cart":
        cart = CART.get(user_id, [])
        if not cart:
            await update.message.reply_text("Your cart is empty.")
        else:
            msg = "Your cart:\n" + "\n".join([f"{item['name']} - ₹{item['price']}" for item in cart])
            await update.message.reply_text(msg)
        return SELECTING
    elif text == "Checkout":
        cart = CART.get(user_id, [])
        if not cart:
            await update.message.reply_text("Your cart is empty.")
            return SELECTING
        total = sum(item['price'] for item in cart)
        await update.message.reply_text(
            f"Thank you for shopping! Your total is ₹{total}.\n\nPlease pay using the QR code below and send the payment confirmation.",
        )
        qr_path = r"c:\Users\thead\OneDrive\Desktop\Aditya\new_qr.jpg"
        try:
            with open(qr_path, "rb") as qr_file:
                await update.message.reply_photo(
                    photo=qr_file,
                    caption="Scan the QR code to pay."
                )
        except FileNotFoundError:
            await update.message.reply_text("QR code image not found. Please contact admin.")
        await update.message.reply_text(
            "After payment, take a screenshot of your invoice and send it to this group for verification:\n"
            "https://t.me/+BkKPvi3tPNEzMDg1\n\n"
            "You can also send your payment proof directly to the admin on Telegram: @theadicoder\n\n"
            "Once you send the screenshot and your purchase is verified by the admin, your plan will be activated within one minute.\n\n"
            "For any help, message on WhatsApp: +966 57 017 6207"
        )
        # --- Auto-generate and send invoice ---
        invoice_id = f"INV{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"
        user = update.effective_user
        invoice_lines = [
            f"🧾 *Invoice*",
            f"Invoice ID: `{invoice_id}`",
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"User: {user.full_name} (@{user.username if user.username else 'N/A'})",
            f"User ID: {user_id}",
            "",
            "Items:"
        ]
        for item in cart:
            invoice_lines.append(f"- {item['name']} : ₹{item['price']}")
        invoice_lines.append(f"\n*Total*: ₹{total}")
        invoice_lines.append("\nThank you for your purchase!")
        invoice_text = "\n".join(invoice_lines)
        await update.message.reply_markdown(invoice_text)
        # Send invoice to group
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"New Checkout:\n\n{invoice_text}",
            parse_mode="Markdown"
        )
        # Save purchase for admin/owner
        PURCHASE_HISTORY.append(invoice_text)
        # --- End invoice ---
        CART[user_id] = []
        return ConversationHandler.END
    else:
        for product in PRODUCTS:
            if product["name"] == text:
                CART[user_id].append(product)
                await update.message.reply_text(
                    f"Added {product['name']} to your cart.\n\nType 'Checkout' to pay or add more products."
                )
                break
        else:
            await update.message.reply_text("Please select a valid product.")
        return SELECTING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Thank you for visiting the shop!")
    return ConversationHandler.END

# --- Owner/Admin Features ---

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def last_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if PURCHASE_HISTORY:
        last = PURCHASE_HISTORY[-1]
        await update.message.reply_text(f"Last Purchase:\n{last}")
    else:
        await update.message.reply_text("No purchases yet.")

async def new_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if PURCHASE_HISTORY:
        await update.message.reply_text("All Purchases:\n" + "\n\n".join(PURCHASE_HISTORY[-10:]))
    else:
        await update.message.reply_text("No purchases yet.")

async def total_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    await update.message.reply_text(f"Total users who started the bot: {len(USERS)}")

async def add_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    feature = " ".join(context.args)
    if not feature:
        await update.message.reply_text("Usage: /add_feature <feature description>")
        return
    await update.message.reply_text(f"Feature noted: {feature}\n(You can implement this in the code.)")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /ban_user <user_id>")
        return
    ban_id = int(context.args[0])
    if ban_id in USERS:
        BANNED_USERS.add(ban_id)
        await update.message.reply_text(f"User {ban_id} banned from bot usage (soft ban).")
    else:
        await update.message.reply_text("User ID not found.")

async def show_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Your Telegram User ID: {user.id}")

async def admin_report_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    ADMIN_CHAT.add(user_id)
    # Prepare statistics
    total_users = len(USERS)
    user_ids = ", ".join(str(uid) for uid in USERS)
    last = PURCHASE_HISTORY[-1] if PURCHASE_HISTORY else "No purchases yet."
    latest = "\n\n".join(PURCHASE_HISTORY[-10:]) if PURCHASE_HISTORY else "No purchases yet."
    banned = ", ".join(str(uid) for uid in BANNED_USERS) if BANNED_USERS else "None"
    msg = (
        "🛡️ *Admin Full Power Activated!*\n"
        "You now have all access and control over the bot.\n\n"
        f"👥 *Total Users*: {total_users}\n"
        f"🆔 *All User IDs*: {user_ids}\n"
        f"🚫 *Banned Users*: {banned}\n"
        f"\n🛒 *Last Purchase*:\n{last}\n"
        f"\n🛒 *Latest 10 Purchases*:\n{latest}\n"
        "\n*Admin Commands:*\n"
        "/last_purchase - Show last purchase\n"
        "/new_purchases - Show last 10 purchases\n"
        "/total_members - Show total users\n"
        "/add_feature <desc> - Note a feature\n"
        "/ban_user <user_id> - Ban user\n"
        "/myid - Show your Telegram user ID\n"
        "/stop_admin_chat - Stop admin chat mode\n"
        "\nType anything to chat with the bot in admin mode."
    )
    await update.message.reply_markdown(msg)

async def stop_admin_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_CHAT:
        ADMIN_CHAT.remove(user_id)
        await update.message.reply_text("Admin chat mode disabled.")
    else:
        await update.message.reply_text("Admin chat mode was not enabled.")

async def admin_casual_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    user_id = update.effective_user.id
    if not BOT_ACTIVE and not is_admin(user_id):
        return
    # Abuse/spam check
    if await check_abuse_and_spam(update, context):
        return
    if user_id in ADMIN_CHAT:
        await update.message.reply_text(f"Admin ({user_id}), you said: {update.message.text}")

async def admin_off_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    BOT_ACTIVE = False
    await update.message.reply_text("Bot is now OFF for all users (except admin commands).")

async def admin_on_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    BOT_ACTIVE = True
    await update.message.reply_text("Bot is now ON for all users.")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /Add_Admin <username or user_id>")
        return
    arg = context.args[0]
    # Try to parse as user_id, else treat as username
    try:
        new_admin_id = int(arg)
        ADMIN_IDS.add(new_admin_id)
        await update.message.reply_text(f"User ID {new_admin_id} added as admin.")
    except ValueError:
        # Search USERS for username
        username = arg.lstrip('@').lower()
        found = False
        for uid in USERS:
            # Get user info from context if available
            chat_member = None
            try:
                chat_member = await context.bot.get_chat_member(GROUP_CHAT_ID, uid)
            except Exception:
                pass
            if chat_member and chat_member.user.username and chat_member.user.username.lower() == username:
                ADMIN_IDS.add(uid)
                await update.message.reply_text(f"User @{username} (ID: {uid}) added as admin.")
                found = True
                break
        if not found:
            await update.message.reply_text("Username not found among users. Please provide a valid user ID or username.")

# Remove or comment out the debug handler after you get the correct chat ID:
# app.add_handler(MessageHandler(filters.ALL, print_chat_id))  # Remove or comment this line

# To fix the error:
# Install the python-telegram-bot library using pip:
# pip install python-telegram-bot --upgrade

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_product)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    # Admin/Owner commands (support both with and without underscores)
    app.add_handler(CommandHandler(["last_purchase", "lastpurchase"], last_purchase))
    app.add_handler(CommandHandler(["new_purchases", "newpurchases"], new_purchases))
    app.add_handler(CommandHandler(["total_members", "totalmembers"], total_members))
    app.add_handler(CommandHandler(["add_feature", "addfeature"], add_feature))
    app.add_handler(CommandHandler(["ban_user", "banuser"], ban_user))
    app.add_handler(CommandHandler("myid", show_user_id))
    app.add_handler(CommandHandler(["Admin_report_me", "admin_report_me"], admin_report_me))
    app.add_handler(CommandHandler(["stop_admin_chat", "stopadminchat"], stop_admin_chat))
    app.add_handler(CommandHandler(["admin_off_bot", "adminoffbot"], admin_off_bot))
    app.add_handler(CommandHandler(["admin_on_bot", "adminonbot"], admin_on_bot))
    app.add_handler(CommandHandler(["Add_Admin", "add_admin"], add_admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_casual_chat))  # For admin chat
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
