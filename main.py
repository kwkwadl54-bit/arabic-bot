import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from easy_pil import Editor, Canvas, Font
from keep_alive import keep_alive
import aiohttp
import io
import os
import json
import random

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

BANNED_WORDS = ["كواد", "كحبه", "فاشل"]


def save_data(data):
    with open('users.json', 'w') as f:
        json.dump(data, f)


def load_data():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {}


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="!مساعدة للأوامر")
    )
    synced = await bot.tree.sync()
    print(f"✅ البوت متصل بنجاح: {bot.user}")
    print(f"📡 عدد السيرفرات: {len(bot.guilds)}")
    print(f"🔄 تم مزامنة {len(synced)} أمر slash")


async def build_welcome_image(member):
    async with aiohttp.ClientSession() as session:
        async with session.get(str(member.display_avatar.with_size(256).url)) as resp:
            avatar_bytes = io.BytesIO(await resp.read())

    background = Editor(Canvas((900, 300), color="#1a1a2e"))
    avatar_editor = Editor(avatar_bytes).resize((220, 220)).circle_image()
    background.paste(avatar_editor, (40, 40))

    background.rectangle((290, 0), width=4, height=300, color="#7289DA")

    welcome_font = Font.poppins(size=32, variant="bold")
    name_font = Font.poppins(size=44, variant="bold")
    server_font = Font.poppins(size=26)

    background.text((310, 50), "أهلاً وسهلاً بك!", font=welcome_font, color="#7289DA")
    background.text((310, 110), str(member.name), font=name_font, color="#FFFFFF")
    background.text((310, 185), f"في سيرفر  {member.guild.name}", font=server_font, color="#99AAB5")
    background.text((310, 235), f"عدد الأعضاء: {member.guild.member_count}", font=server_font, color="#99AAB5")

    return discord.File(fp=io.BytesIO(background.image_bytes), filename="welcome.png")


@bot.event
async def on_member_join(member):
    print(f"✅ on_member_join triggered for: {member.name}")
    channel = bot.get_channel(1490735082158424135)
    if channel is None:
        print("❌ لم يتم العثور على قناة الترحيب!")
        return

    file = await build_welcome_image(member)
    await channel.send(
        content=f"نورت السيرفر يا بطل {member.mention}! بوجودك صرنا **{member.guild.member_count}** عضو",
        file=file,
    )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()

    print(f"📨 رسالة من {message.author}: {content!r}")

    member = message.guild.get_member(message.author.id) if message.guild else None
    is_admin = member and member.guild_permissions.administrator

    if not is_admin and any(word in content for word in ["http://", "https://", "discord.gg"]):
        await message.delete()
        warning = await message.channel.send(f"⛔ {message.author.mention} ممنوع إرسال الروابط في هذا السيرفر!")
        try:
            until = datetime.now(timezone.utc) + timedelta(minutes=10)
            await member.timeout(until, reason="إرسال رابط ممنوع")
        except discord.Forbidden:
            pass
        await warning.delete(delay=5)
        return

    if not is_admin and any(word in content.lower() for word in BANNED_WORDS):
        try:
            await message.delete()
            warning = await message.channel.send(f"⚠️ {message.author.mention}، ممنوع استخدام كلمات غير لائقة في السيرفر!")
            await warning.delete(delay=5)
        except discord.Forbidden:
            print("البوت يحتاج صلاحية (Manage Messages) لمسح الرسائل.")
        return

    greetings = ["السلام عليكم", "سلام عليكم"]
    if any(g in content for g in greetings):
        await message.channel.send(f"وعليكم السلام والرحمة، منور السيرفر يا بطل {message.author.mention}!")

    if "هلا" in content and not content.startswith(bot.command_prefix):
        await message.channel.send(f"هلا بيك يا بطل نورت السيرفر {message.author.mention}")

    if content.startswith("مسح") and not content.startswith(bot.command_prefix):
        parts = content.split()
        amount = 10
        if len(parts) > 1 and parts[1].isdigit():
            amount = int(parts[1])
        if amount < 1 or amount > 100:
            await message.channel.send("❌ يرجى اختيار عدد بين 1 و 100.")
        else:
            if member and member.guild_permissions.manage_messages:
                deleted = await message.channel.purge(limit=amount + 1)
                msg = await message.channel.send(f"✅ تم مسح **{len(deleted) - 1}** رسالة بنجاح!")
                await msg.delete(delay=3)
            else:
                await message.channel.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")

    users = load_data()
    user_id = str(message.author.id)
    if user_id not in users:
        users[user_id] = {'xp': 0, 'level': 1}

    users[user_id]['xp'] += random.randint(10, 20)
    xp = users[user_id]['xp']
    lvl = users[user_id]['level']

    if xp >= lvl * 100:
        users[user_id]['level'] += 1
        await message.channel.send(f"🎉 كفو {message.author.mention}! صعدت للـ لفل **{lvl + 1}**")

    save_data(users)
    await bot.process_commands(message)


@bot.command(name="test")
async def test(ctx):
    await ctx.send("✅ Working!")


@bot.command(name="test_join")
async def test_join(ctx):
    member = ctx.author
    channel = bot.get_channel(1490735082158424135) or ctx.channel
    file = await build_welcome_image(member)
    await channel.send(
        content=f"نورت السيرفر يا بطل {member.mention}! بوجودك صرنا **{ctx.guild.member_count}** عضو",
        file=file,
    )


@bot.command(name="rank")
async def rank(ctx):
    users = load_data()
    user_id = str(ctx.author.id)
    if user_id in users:
        lvl = users[user_id]['level']
        xp = users[user_id]['xp']
        needed = lvl * 100
        embed = discord.Embed(
            title=f"📊 مستوى {ctx.author.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="🏆 المستوى", value=f"**{lvl}**", inline=True)
        embed.add_field(name="⭐ الخبرة", value=f"**{xp} / {needed}**", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("اكتب رسائل أكثر حتى يبين مستواك!")


@bot.command(name="هلا")
async def hello(ctx):
    await ctx.send(f"هلا بيك يا بطل نورت السيرفر {ctx.author.mention}")


@bot.command(name="مسح")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    if amount < 1 or amount > 100:
        await ctx.send("❌ يرجى اختيار عدد بين 1 و 100.")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"✅ تم مسح **{len(deleted) - 1}** رسالة بنجاح!")
    await msg.delete(delay=3)


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ يرجى إدخال رقم صحيح. مثال: `!مسح 10`")


@bot.tree.command(name="مسح", description="مسح عدد معين من الرسائل")
@app_commands.describe(amount="عدد الرسائل اللي تريد تمسحها")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_clear(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ حدد رقم بين 1 و 100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم مسح **{len(deleted)}** رسالة بنجاح!", ephemeral=True)


@slash_clear.error
async def slash_clear_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("🚫 ما عندك صلاحية 'إدارة الرسائل' لاستخدام هذا الأمر!", ephemeral=True)


@bot.command(name="مساعدة")
async def help_command(ctx):
    embed = discord.Embed(
        title="📋 قائمة الأوامر",
        description="إليك جميع الأوامر المتاحة:",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="!هلا",
        value="يرحب فيك البوت باسمك",
        inline=False,
    )
    embed.add_field(
        name="!مسح [عدد]",
        value="مسح عدد محدد من الرسائل (الافتراضي: 10)",
        inline=False,
    )
    embed.add_field(
        name="!مساعدة",
        value="عرض قائمة الأوامر المتاحة",
        inline=False,
    )
    embed.add_field(
        name="!بينغ",
        value="التحقق من سرعة استجابة البوت",
        inline=False,
    )
    embed.add_field(
        name="!معلومات",
        value="عرض معلومات عن السيرفر",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="بينغ")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 البينغ: **{latency}ms**")


@bot.command(name="معلومات")
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"معلومات سيرفر {guild.name}",
        color=discord.Color.gold(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 المالك", value=guild.owner, inline=True)
    embed.add_field(name="👥 عدد الأعضاء", value=guild.member_count, inline=True)
    embed.add_field(name="📝 عدد القنوات", value=len(guild.channels), inline=True)
    embed.add_field(name="📅 تاريخ الإنشاء", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.send(embed=embed)


keep_alive()

token = os.environ.get("DISCORD_TOKEN")
if not token:
    print("❌ لم يتم العثور على DISCORD_TOKEN في المتغيرات البيئية!")
else:
    bot.run(token)
