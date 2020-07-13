#!/usr/bin/env python3

from discord import Status
from discord.ext import commands
import os
from asyncio import subprocess
from discord.errors import NoMoreItems
import json
import util

warning = "⚠"

bot = commands.Bot(
    max_messages=50,
    fetch_offline_members=False,
    guild_subscriptions=False,
    command_prefix="_",
    help_command=commands.DefaultHelpCommand(no_category="Commands:"),
)

# thank you to https://github.com/johnnyapol/AmpRemover
@bot.listen()
async def on_message(message):
    if util.check_if_amp(message.content):
        urls = util.get_amp_urls(message.content)
        non_amp = util.get_canonicals(urls, False)

        msg_text = "Non-AMP Urls:"
        base_len = len(msg_text)

        for url in non_amp:
            if len(url) == 0:
                continue
            msg_text = f"{msg_text}\n{url}"

        if len(msg_text) != base_len:
            await message.channel.send(msg_text)


@bot.event
async def on_ready():
    print("We have logged in as {0}!".format(bot.user))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(str(error))


@bot.command()
async def ping(ctx):
    """send a pon"""
    await ctx.send("pon")


async def historify(ctx, args):
    if not args:
        msg = await ctx.history(limit=1, before=ctx.message).next()
        args = [msg.clean_content]
    else:
        return args


@bot.command()
async def yturl(ctx, *, arg=None):
    """get direct url of media link"""
    arg = await historify(ctx, arg)
    if not arg:
        return

    proc = await subprocess.create_subprocess_exec(
        "youtube-dl",
        "-f",
        "best",
        "-g",
        arg,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    data = await proc.stdout.read()
    line = data.decode()
    if await proc.wait() != 0:
        line = warning + " " + line

    await ctx.send(line)


@bot.command()
async def yt(ctx, *, arg):
    """get website url from query"""
    if not arg:
        return
    proc = await subprocess.create_subprocess_exec(
        "youtube-dl",
        "-f",
        "best",
        "-j",
        "--simulate",
        arg,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    result = json.loads(await proc.stdout.read())
    await proc.wait()

    await ctx.send(result["webpage_url"])


safelist = [
    "-g",
    "-e",
    "--get-url",
    "--get-title",
    "--get-id",
    "--get-thumbnail",
    "--get-description",
    "--get-duration",
    "--get-filename",
    "--list-thumbnails",
    "-f",
    "-F",
    "--format",
    "--list-formats",
]


@bot.command()
async def ytargs(ctx, *args):
    """advanced command that special arguments, needs quoting"""
    if not args:
        return
    for x in args:
        if x.startswith("-") and not x in safelist:
            await ctx.message.add_reaction("❌")
            return
    proc = await subprocess.create_subprocess_exec(
        "youtube-dl",
        "--simulate",
        *args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    data = await proc.stdout.read()
    line = data.decode()
    line = line.rstrip("\n")
    if await proc.wait() != 0:
        line = warning + " " + line

    await ctx.send(line)


@bot.command()
async def safeargs(ctx):
    """print safe arguments"""
    await ctx.send(", ".join(safelist))


@bot.command()
async def say(ctx, *, arg):
    if ctx.author.id == 147077474222604288:
        await ctx.send(arg)


@bot.command()
async def nick(ctx, *, arg):
    await ctx.guild.me.edit(nick=arg)


bot.run(os.getenv("TOKEN"))
