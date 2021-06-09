from dotenv import load_dotenv
import asyncio
import os
import urllib.parse
from discord import Embed, Colour, Intents
from discord.ext.commands import Bot
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType

from bot.deta import DetaManager

load_dotenv()

bot = Bot("!", intents=Intents.all())
db = DetaManager(os.getenv('DETA_KEY'))

BUTTON_LABEL_JOIN = '参加'
BUTTON_LABEL_LEAVE = '退出'
BUTTON_LABEL_TWITTER = 'Twitterで募集'
BUTTON_LABEL_QK1 = '休憩1'
BUTTON_LABEL_QK2 = '休憩2'
BUTTON_LABEL_QK3 = '休憩3'
BUTTON_LABEL_QK4 = '休憩4'


@bot.event
async def on_ready():
    DiscordComponents(bot)
    print(f"Logged in as {bot.user}!")


@bot.event
async def on_button_click(res):
    """
    Possible interaction types:
    - Pong
    - ChannelMessageWithSource
    - DeferredChannelMessageWithSource
    - DeferredUpdateMessage
    - UpdateMessage
    """

    # 休憩処理がタイムアウトになるので先に返す
    await res.respond(type=InteractionType.UpdateMessage)

    # 参加イベント
    if res.component.label == BUTTON_LABEL_JOIN:
        db.add_member(res.user, res.message.id)
        if len(db.get_pooled_qk_many(res.user.id, res.message.id)) == 0:
            db.add_pooled_qk(res.user.id, res.user.mention, res.message.id)

    # 退室イベント
    if res.component.label == BUTTON_LABEL_LEAVE:
        db.delete_member(res.user.id, res.message.id)
        db.delete_qk(res.user.id, res.message.id)
        db.delete_pooled_qks(res.user.id, res.message.id)

    # 休憩イベント
    if res.component.label in [BUTTON_LABEL_QK1, BUTTON_LABEL_QK2, BUTTON_LABEL_QK3, BUTTON_LABEL_QK4]:
        qk_size = [BUTTON_LABEL_QK1, BUTTON_LABEL_QK2, BUTTON_LABEL_QK3, BUTTON_LABEL_QK4].index(res.component.label) + 1
        select_qk(res.message.id, qk_size)

    players = db.get_members(res.message.id)
    players_qk = db.get_qks(res.message.id)

    embed = create_embed(message_id=res.message.id, members_all=players, members_qk=players_qk)
    mention_qk = ' '.join([x['mention'] for x in players_qk])

    await res.message.edit(
        content=mention_qk,
        embed=embed,
    )


@bot.command()
async def qk(ctx):

    invite = await ctx.channel.create_invite()
    tweet_url = create_tweet_url(ctx.guild, invite.url)

    players = []
    players_qk = []

    btn_message = await ctx.send(
        embed=create_embed(),
        components=[
            [
                Button(style=ButtonStyle.green, label=BUTTON_LABEL_JOIN),
                Button(style=ButtonStyle.red, label=BUTTON_LABEL_LEAVE),
                Button(style=ButtonStyle.URL, label=BUTTON_LABEL_TWITTER, url=tweet_url),
            ],
            [
                Button(style=ButtonStyle.blue, label=BUTTON_LABEL_QK1),
                Button(style=ButtonStyle.blue, label=BUTTON_LABEL_QK2),
                Button(style=ButtonStyle.blue, label=BUTTON_LABEL_QK3),
                Button(style=ButtonStyle.blue, label=BUTTON_LABEL_QK4),
            ]
        ],
    )
    await ctx.message.delete()

    embed = create_embed(message_id=btn_message.id)
    await btn_message.edit(embed=embed)

    db_messages = next(db.messages.fetch({'id': btn_message.id}))
    if len(db_messages) == 0:
        db.add_message(ctx, btn_message, db.MessageType.QK)


def get_mention_field_value(values):
    v = [x['mention'] for x in values] if len(values) > 0 else ['-']
    return '\n'.join(v)


def create_embed(message_id='', members_all=[], members_qk=[]):
    embed = Embed(
        title=f'プラベ【{message_id}】',
        colour=Colour.from_rgb(79, 167, 255),
    )
    mention_all = get_mention_field_value(members_all)
    mention_qk = get_mention_field_value(members_qk)

    embed.add_field(name='🔵参加者', value=mention_all)
    embed.add_field(name='🔴休憩', value=mention_qk)
    return embed


def create_tweet_url(guild, invite_url):
    hashtags = ' '.join(['#RocketLeague', '#ロケットリーグ', '#プラベ', '#discord'])
    text = [
        '【プラベ募】'
        f'{guild.name}サーバーでプラベ募集中！',
        'だれでも歓迎🙌',
        '',
        hashtags,
        invite_url,
    ]
    s = '\n'.join(text)
    s_quote = urllib.parse.quote(s)
    url = 'https://twitter.com/intent/tweet?text=%s'
    return url % s_quote


def select_qk(message_id, qk_size):
    exclude_qk_members = []
    members_all = db.get_members(message_id)
    pooled_qks = db.get_pooled_qks(message_id)

    # 休憩情報クリア
    for x in db.get_qks(message_id):
        db.delete_qk(x['member_id'], message_id)

    # プールが不足したら補充
    if len(pooled_qks) < qk_size:
        for x in pooled_qks:
            # 残りのプールを一旦すべて削除
            exclude_qk_members.append(x['member_id'])
            db.delete_pooled_qks(x['member_id'], message_id)

        for m in members_all:
            pooled_qks.append(db.add_pooled_qk(m['id'], m['mention'], message_id))

    results = pooled_qks[:qk_size]

    # 休憩ユーザーを追加
    for result in results:
        # 補充分のプールから休憩ユーザーを削除
        if result['member_id'] not in exclude_qk_members:
            db.delete_pooled_qks(result['member_id'], message_id)
        db.add_qk(result['member_id'], result['mention'], message_id)


bot.run(os.getenv('DISCORD_TOKEN'))
