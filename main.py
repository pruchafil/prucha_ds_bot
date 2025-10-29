import datetime
from logging import Logger

from dotenv import load_dotenv
import discord
import os
import channels
import pings

from bot import DiscordBot
from logging_formatter import setup_logger
from spam_filter import check_spam, SpamType, is_ping
from user_actions import timeout_user

logger: Logger
bot : DiscordBot

def main():
    load_dotenv()
    intents = discord.Intents.default()
    global logger
    logger = setup_logger()
    global bot
    bot = DiscordBot(logger, intents, os.getenv("GUILD"))

if __name__ == '__main__':
    main()

guild = os.getenv("GUILD")

@bot.tree.command(guild=discord.Object(id = guild), name="bot", description="description")
async def slash_command(interaction: discord.Interaction):
    await interaction.response.send_message("Jsem chytrej bot, kterého napsal nejlepší programátor "
                                            "na zeměkouli: www.youtube.com/@programmingCZ")

@bot.tree.command(guild=discord.Object(id = guild), name="popis_her", description="popis her pro dementy")
async def slash_command(interaction: discord.Interaction):
    s = ""

    for i in range(len(pings.pings_all)):
        s += pings.pings_all[i] + " - " + pings.pings_trans[i]
        s += "\n"

    await interaction.response.send_message(s.removesuffix("\n"))

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    spam_type = check_spam(message)

    already_got_yelled_at = False

    if spam_type != SpamType.NONE:
        already_got_yelled_at = True
        if spam_type == SpamType.SMALL:
            await message.reply("Klidni se kurva nebo bude kick.", silent=True, delete_after=20)
        else:
            coef = (int(spam_type) - 1)
            minutes = coef ** (10/3)
            await message.reply("Táhni do píči, cache hit = " + str(minutes) + " minut timeout")
            await timeout_user(logger, message.author, datetime.timedelta(minutes=minutes), reason="spam")

    channel = message.channel
    c_name = channel.name

    if c_name in channels.channel_announcements and is_ping(message):
        await message.delete()
        if not already_got_yelled_at:
            await channel.send(f"Si děláš prdel? Pingovat v oznamovací místnosti je fakt sračka! "
                               f"{message.author.mention}", silent=True, delete_after=20)

        return

    if c_name in channels.channel_warning_ping and is_ping(message):
        if not already_got_yelled_at:
            await message.reply("Pingují jen otravní kokoti, pokud chceš hrát a seš takovej krypl, "
                               "že nevíš co znamenají jaké role, tak použij \"/popis_her\".", delete_after=20)
    elif c_name in channels.channel_no_ping and is_ping(message):
        await message.delete()
        if not already_got_yelled_at:
            await channel.send(f"Zde je pingování zakázáno! {message.author.mention}", silent=True, delete_after=20)

        return

    if c_name in channels.channel_url_only and not "http" in message.content:
        await message.delete()
        if not already_got_yelled_at:
            await channel.send(f"Zde je povoleno posílat pouze odkazy! {message.author.mention}",
                                silent=True, delete_after=20)
        return

bot.run(os.getenv("TOKEN"))