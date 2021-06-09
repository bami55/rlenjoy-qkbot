from datetime import datetime
from enum import IntEnum, auto

from deta import Deta


class DetaManager():

    class MessageType(IntEnum):
        QK = auto()
        BOSYU = auto()

    def __init__(self, key):
        self.deta = Deta(key)
        self.messages = self.get_or_create_table('messages')
        self.members = self.get_or_create_table('members')
        self.qks = self.get_or_create_table('qks')
        self.pooled_qks = self.get_or_create_table('pooled_qks')

    def get_or_create_table(self, name):
        return self.deta.Base(name)

    def get_message(self, message_id):
        m = next(self.messages.fetch({'id': str(message_id)}))
        return m[0] if len(m) > 0 else None

    def add_message(self, ctx, btn_message, message_type):
        now = datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.messages.put({
            'id': str(btn_message.id),
            'guild_id': str(ctx.guild.id),
            'guild_name': ctx.guild.name,
            'channel_id': str(btn_message.channel.id),
            'channel_name': btn_message.channel.name,
            'message_author_id': str(ctx.message.author.id),
            'message_author_name': ctx.message.author.name,
            'message_author_display_name': ctx.message.author.display_name,
            'message_type': int(message_type),
            'created_at': now,
            'updated_at': now,
        })

    def get_members(self, message_id):
        m = next(self.members.fetch({'message_id': str(message_id)}))
        return sorted(m, key=lambda x: x['updated_at'])

    def get_member(self, member_id, message_id):
        m = next(self.members.fetch({'id': str(member_id), 'message_id': str(message_id)}))
        return m[0] if len(m) > 0 else None

    def add_member(self, member, message_id):
        now = datetime.now().strftime('%Y%m%d%H%M%S%f')
        m = self.get_member(str(member.id), str(message_id))
        if m is None:
            return self.members.put({
                'id': str(member.id),
                'name': member.name,
                'display_name': member.display_name,
                'mention': member.mention,
                'message_id': str(message_id),
                'created_at': now,
                'updated_at': now,
            })
        else:
            return None

    def delete_member(self, member_id, message_id):
        m = self.get_member(str(member_id), str(message_id))
        if m:
            self.members.delete(m['key'])

    def get_qks(self, message_id):
        q = next(self.qks.fetch({'message_id': str(message_id)}))
        return sorted(q, key=lambda x: x['updated_at'])

    def get_qk(self, member_id, message_id):
        q = next(self.qks.fetch({'member_id': str(member_id), 'message_id': str(message_id)}))
        return q[0] if len(q) > 0 else None

    def add_qk(self, member_id, mention, message_id):
        now = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return self.qks.put({
            'member_id': str(member_id),
            'mention': mention,
            'message_id': str(message_id),
            'created_at': now,
            'updated_at': now,
        })

    def delete_qk(self, member_id, message_id):
        q = self.get_qk(str(member_id), str(message_id))
        if q:
            self.qks.delete(q['key'])

    def get_pooled_qks(self, message_id):
        q = next(self.pooled_qks.fetch({'message_id': str(message_id)}))
        return sorted(q, key=lambda x: x['updated_at'])

    def get_pooled_qk_many(self, member_id, message_id):
        q = next(self.pooled_qks.fetch({'member_id': str(member_id), 'message_id': str(message_id)}))
        return q

    def add_pooled_qk(self, member_id, mention, message_id):
        now = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return self.pooled_qks.put({
            'member_id': str(member_id),
            'mention': mention,
            'message_id': str(message_id),
            'created_at': now,
            'updated_at': now,
        })

    def delete_pooled_qks(self, member_id, message_id):
        qs = self.get_pooled_qk_many(str(member_id), str(message_id))
        for q in qs:
            self.pooled_qks.delete(q['key'])
