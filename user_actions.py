from logging import Logger, exception

import discord
import datetime

async def timeout_user(logger: Logger, user: discord.User | discord.Member, until: datetime.timedelta, reason: str):
    try:
        await user.timeout(until, reason=reason)
        logger.info(f"Successful timeout %s for %i minutes", user, until.min)
    except discord.Forbidden as e:
        logger.error("failed to blocked user %s %s", user, e.text)

