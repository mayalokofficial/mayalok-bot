import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Config
TOKEN = "8804554324:AAGnGvkbSIQJxbY0NAHh6JhNxs5Aq1hdDpM"
ADMIN_ID = None  # পরে বসাবো

# Database (simple dict)
users = {}
videos = {}
scripts = {}
pending_videos = []

logging.basicConfig(level=logging.INFO)

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    
    if user_id not in users:
        users[user_id] = {
            "name": name,
            "approved": False,
            "balance": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "bkash": ""
        }
        # Admin কে নোটিফাই করো
        if ADMIN_ID:
            keyboard = [
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_user_{user_id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"reject_user_{user_id}")]
            ]
            await context.bot.send_message(
                ADMIN_ID,
                f"🆕 নতুন মেম্বার!\n👤 নাম: {name}\n🆔 ID: {user_id}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        await update.message.reply_text(
            f"🌿 *মায়ালোকে স্বাগতম {name}!*\n\n"
            f"আপনার রেজিস্ট্রেশন হয়েছে।\n"
            f"Admin অ্যাপ্রুভ করলে কাজ শুরু করতে পারবেন।\n\n"
            f"অনুগ্রহ করে অপেক্ষা করুন... ⏳",
            parse_mode="Markdown"
        )
    else:
        await show_menu(update, context)

# MENU
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in users or not users[user_id]["approved"]:
        await update.message.reply_text("⏳ আপনার একাউন্ট এখনো অ্যাপ্রুভ হয়নি।")
        return
    
    keyboard = [
        [InlineKeyboardButton("📋 আজকের স্ক্রিপ্ট", callback_data="show_script")],
        [InlineKeyboardButton("🎬 ভিডিও জমা দিন", callback_data="submit_video")],
        [InlineKeyboardButton("💰 আমার আয়", callback_data="my_balance")],
        [InlineKeyboardButton("💸 উইথড্রল", callback_data="withdraw")],
        [InlineKeyboardButton("📜 নিয়মকানুন", callback_data="rules")],
        [InlineKeyboardButton("🏆 লিডারবোর্ড", callback_data="leaderboard")]
    ]
    
    await update.message.reply_text(
        "🌿 *মায়ালোক ফুটেজ টিম*\n\nকী করতে চান?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# CALLBACK HANDLER
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # User Approve/Reject
    if data.startswith("approve_user_"):
        uid = int(data.split("_")[2])
        if uid in users:
            users[uid]["approved"] = True
            await context.bot.send_message(
                uid,
                "✅ *অভিনন্দন!*\n\nআপনার একাউন্ট অ্যাপ্রুভ হয়েছে!\n/menu লিখে কাজ শুরু করুন।",
                parse_mode="Markdown"
            )
            await query.edit_message_text(f"✅ User {uid} অ্যাপ্রুভ করা হয়েছে।")

    elif data.startswith("reject_user_"):
        uid = int(data.split("_")[2])
        await context.bot.send_message(uid, "❌ দুঃখিত, আপনার একাউন্ট অ্যাপ্রুভ হয়নি।")
        await query.edit_message_text(f"❌ User {uid} রিজেক্ট করা হয়েছে।")

    # Script দেখা
    elif data == "show_script":
        if scripts:
            script_text = scripts.get("current", "এখনো কোনো স্ক্রিপ্ট আপলোড হয়নি।")
            await query.edit_message_text(f"📋 *আজকের স্ক্রিপ্ট:*\n\n{script_text}", parse_mode="Markdown")
        else:
            await query.edit_message_text("📋 এখনো কোনো স্ক্রিপ্ট আপলোড হয়নি।")

    # ভিডিও জমা
    elif data == "submit_video":
        context.user_data["waiting_video"] = True
        await query.edit_message_text(
            "🎬 *ভিডিও জমা দিন*\n\n"
            "ভিডিও লিংক পাঠান এই ফরম্যাটে:\n\n"
            "`প্যারা নম্বর | ভিডিও লিংক | সোর্স`\n\n"
            "উদাহরণ:\n`1 | https://pexels.com/xxx | Pexels`",
            parse_mode="Markdown"
        )

    # ব্যালেন্স
    elif data == "my_balance":
        if user_id in users:
            u = users[user_id]
            await query.edit_message_text(
                f"💰 *আমার আয়*\n\n"
                f"✅ মোট Approve: {u['total_approved']} টি\n"
                f"❌ মোট Reject: {u['total_rejected']} টি\n"
                f"💵 বর্তমান ব্যালেন্স: {u['balance']} টাকা\n\n"
                f"_প্রতিটি Approve = ২ টাকা_",
                parse_mode="Markdown"
            )

    # উইথড্রল
    elif data == "withdraw":
        if user_id in users:
            balance = users[user_id]["balance"]
            if balance < 50:
                await query.edit_message_text(
                    f"💸 *উইথড্রল*\n\n"
                    f"আপনার ব্যালেন্স: {balance} টাকা\n\n"
                    f"⚠️ মিনিমাম ৫০ টাকা হলে উইথড্রল করা যাবে।",
                    parse_mode="Markdown"
                )
            else:
                context.user_data["waiting_bkash"] = True
                await query.edit_message_text(
                    f"💸 আপনার ব্যালেন্স: {balance} টাকা\n\n"
                    f"বিকাশ নম্বর পাঠান:",
                    parse_mode="Markdown"
                )

    # নিয়মকানুন
    elif data == "rules":
        await query.edit_message_text(
            "📜 *নিয়মকানুন*\n\n"
            "১. শুধু কপিরাইট ফ্রি ভিডিও দিতে হবে\n"
            "২. Pexels, Pixabay, Videvo থেকে নিতে হবে\n"
            "৩. লিংকের সাথে সোর্স উল্লেখ করতে হবে\n"
            "৪. একই লিংক দুইবার দেওয়া যাবে না\n"
            "৫. ৩ বার Reject হলে সতর্কতা\n"
            "৬. ৫ বার Reject হলে সাসপেন্ড\n"
            "৭. মিনিমাম ৫০ টাকা হলে উইথড্রল\n\n"
            "✅ প্রতিটি Approve = ২ টাকা",
            parse_mode="Markdown"
        )

    # লিডারবোর্ড
    elif data == "leaderboard":
        sorted_users = sorted(users.items(), key=lambda x: x[1]["total_approved"], reverse=True)
        text = "🏆 *লিডারবোর্ড*\n\n"
        for i, (uid, u) in enumerate(sorted_users[:5], 1):
            text += f"{i}. {u['name']} — {u['total_approved']} টি ✅\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    # Video Approve/Reject
    elif data.startswith("approve_video_"):
        vid_idx = int(data.split("_")[2])
        if vid_idx < len(pending_videos):
            video = pending_videos[vid_idx]
            uid = video["user_id"]
            if uid in users:
                users[uid]["balance"] += 2
                users[uid]["total_approved"] += 1
            pending_videos.pop(vid_idx)
            await context.bot.send_message(
                uid,
                "✅ *আপনার ভিডিও Approve হয়েছে!*\n💰 ২ টাকা যোগ হয়েছে।",
                parse_mode="Markdown"
            )
            await query.edit_message_text("✅ ভিডিও Approve করা হয়েছে।")

    elif data.startswith("reject_video_"):
        vid_idx = int(data.split("_")[2])
        if vid_idx < len(pending_videos):
            video = pending_videos[vid_idx]
            uid = video["user_id"]
            if uid in users:
                users[uid]["total_rejected"] += 1
            pending_videos.pop(vid_idx)
            await context.bot.send_message(
                uid,
                "❌ *আপনার ভিডিও Reject হয়েছে।*\nআরো ভালো মানের ভিডিও দিন।",
                parse_mode="Markdown"
            )
            await query.edit_message_text("❌ ভিডিও Reject করা হয়েছে।")

# MESSAGE HANDLER
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Admin Command
    if text.startswith("/setscript ") and user_id == ADMIN_ID:
        script_text = text.replace("/setscript ", "")
        scripts["current"] = script_text
        await update.message.reply_text("✅ স্ক্রিপ্ট আপলোড হয়েছে!")
        return

    if text.startswith("/setadmin") and ADMIN_ID is None:
        global ADMIN_ID
        ADMIN_ID = user_id
        await update.message.reply_text(f"✅ আপনি Admin হয়েছেন! ID: {user_id}")
        return

    if text == "/menu":
        await show_menu(update, context)
        return

    if text == "/stats" and user_id == ADMIN_ID:
        total = len(users)
        approved = sum(1 for u in users.values() if u["approved"])
        total_pay = sum(u["balance"] for u in users.values())
        await update.message.reply_text(
            f"📊 *Stats*\n\n"
            f"👥 মোট মেম্বার: {total}\n"
            f"✅ Approved: {approved}\n"
            f"💰 মোট পেমেন্ট বাকি: {total_pay} টাকা\n"
            f"⏳ Pending ভিডিও: {len(pending_videos)}",
            parse_mode="Markdown"
        )
        return

    # ভিডিও জমা
    if context.user_data.get("waiting_video"):
        if "|" in text:
            parts = text.split("|")
            if len(parts) >= 2:
                video_data = {
                    "user_id": user_id,
                    "user_name": update.effective_user.first_name,
                    "para": parts[0].strip(),
                    "link": parts[1].strip(),
                    "source": parts[2].strip() if len(parts) > 2 else "Unknown"
                }
                vid_idx = len(pending_videos)
                pending_videos.append(video_data)
                context.user_data["waiting_video"] = False

                if ADMIN_ID:
                    keyboard = [
                        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_video_{vid_idx}"),
                         InlineKeyboardButton("❌ Reject", callback_data=f"reject_video_{vid_idx}")]
                    ]
                    await context.bot.send_message(
                        ADMIN_ID,
                        f"🎬 *নতুন ভিডিও জমা!*\n\n"
                        f"👤 {video_data['user_name']}\n"
                        f"📌 প্যারা: {video_data['para']}\n"
                        f"🔗 লিংক: {video_data['link']}\n"
                        f"📁 সোর্স: {video_data['source']}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                await update.message.reply_text("✅ ভিডিও জমা হয়েছে! Admin রিভিউ করবেন।")
        else:
            await update.message.reply_text("❌ সঠিক ফরম্যাটে দিন:\n`প্যারা | লিংক | সোর্স`", parse_mode="Markdown")

    # বিকাশ নম্বর
    elif context.user_data.get("waiting_bkash"):
        users[user_id]["bkash"] = text
        context.user_data["waiting_bkash"] = False
        balance = users[user_id]["balance"]
        if ADMIN_ID:
            await context.bot.send_message(
                ADMIN_ID,
                f"💸 *উইথড্রল রিকোয়েস্ট!*\n\n"
                f"👤 {update.effective_user.first_name}\n"
                f"💰 পরিমাণ: {balance} টাকা\n"
                f"📱 বিকাশ: {text}",
                parse_mode="Markdown"
            )
        await update.message.reply_text("✅ উইথড্রল রিকোয়েস্ট পাঠানো হয়েছে! Admin শীঘ্রই পাঠাবেন।")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Bot চালু হয়েছে!")
    app.run_polling()

if __name__ == "__main__":
    main()
