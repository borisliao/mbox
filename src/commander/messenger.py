from __future__ import annotations
import asyncio
import discord
from datetime import datetime
from typing import List, Dict
import logging
from src.commander.element.ChatEmbed import ChatEmbed
from src.commander.element.Button import Button
from src.constants import *

class Messenger:
    def __init__(self, default_channel, client, command_channel: discord.TextChannel = None) -> None:
        self.default_channel: discord.TextChannel = default_channel
        self.command_channel: discord.TextChannel = command_channel
        self.client: discord.Client = client
        self.user = client.user
        self.gui: Dict[str, ChatEmbed] = {}
    
    async def setup(self):
        self.set_gui()
        await self.clean_chat()
        await self.send_gui(register_buttons=False)
    
    def set_gui(self) -> None:
        self.gui: Dict[str, ChatEmbed] = {
            'reporter' : ChatEmbed('lyrics', {
                'title': 'Music Box ' + VERSION,
                'description': """
                **Please mute this channel to avoid notification spam!**
                """ + USAGE_TEXT + """
                *Early Access, please report any bugs!*
                """
            }, self.command_channel),
            'queue' : ChatEmbed('queue', {
                'title': 'Queue',
                'description': 'Nothing is in your queue. ' + USAGE_TEXT
            }, self.command_channel),
            'player' : ChatEmbed('player', {
                'title': 'Player',
                'description': 'Nothing is playing. ' + USAGE_TEXT
            }, self.command_channel)
        }
    
    def is_gui(self, message: discord.Message) -> bool:
        if len(message.embeds) == 1:
            for key in self.gui:
                if(self.gui[key].embed.title == message.embeds[0].title):
                    self.gui[key].message = message
                    return True
        return False
    
    async def register_all(self):
        chat_embed: ChatEmbed
        button: Button
        for chat_embed in self.gui.values():
            await chat_embed.register_buttons()

    async def unregister_all(self):
        chat_embed: ChatEmbed
        button: Button
        for chat_embed in self.gui.values():
            if chat_embed.actions:
                for button in chat_embed.actions:
                    await button.remove_all()

    async def clean_chat(self):
        await self.unregister_all()
        counter = 0
        deleted_messages: List[discord.Message]= []
        message: discord.Message
        async for message in self.command_channel.history(limit=101):
            counter += 1
            if (datetime.today() - message.created_at).days > 14:
                counter += 100
            if counter > 100:
                guild = self.command_channel.guild
                await self.command_channel.delete()

                music_box = await guild.create_text_channel(name='music-box')
                topic = 'Music Box controlled channel. Chat in this channel will be deleted. Version ' + VERSION + ' ' + str(hash(music_box))
                await music_box.edit(topic=topic)

                self.command_channel = music_box
                self.set_gui()
                return
            deleted_messages.append(message)
        
        logging.info('deleted_messages: ' + str(len(deleted_messages)))
        await self.command_channel.delete_messages(deleted_messages)
                    
    
    async def notify_action_required(self, err_msg, action_failed, action_sucesss, act_msg):
        text_channel = self.default_channel
        err_str = err_msg
        message_warning = await text_channel.send(err_str + '\n**Click on the toolbox below to auto finish setup!**')
        await message_warning.add_reaction('🧰')
        
        def check(reaction, user):
            return user != self.user and str(reaction.emoji) == '🧰'

        try:
            # Note: Using reaction_add event, which only gets exec when reactions are added to a message in bot cache
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await message_warning.edit(content=err_str+'\n~~Click on the toolbox below to auto finish setup!~~')
            await action_failed(text_channel)
        else:
            await message_warning.edit(content=err_str+'\n' + '**' + act_msg + '**')
            await action_sucesss(text_channel)

    async def send_gui(self, register_buttons = True):
        if self.command_channel:
            for chat_embed in self.gui.values():
                await chat_embed.send(register_buttons=register_buttons)