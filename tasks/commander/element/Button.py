import discord
import asyncio
import logging
from types import FunctionType
from typing import Dict

class Button:
    def __init__(self, emoji, client: discord.Client, *, timeout = None, action: FunctionType = None, action_timeout: FunctionType = None):
        self.emoji = emoji
        self.client = client
        self.timeout = timeout
        self.action = action
        self.action_timeout = action_timeout
        self.coro: Dict[discord.Message, asyncio.Task] = {}
    
    def is_registered(self, message: discord.Message):
        if message in self.coro:
            return True
        return False
    
    # TODO Function needs testing to make sure it doesn't spawn unnessasary threads
    async def register(self, message: discord.Message):
        if type(message) == discord.Message:
            if message not in self.coro:
                await message.add_reaction(self.emoji)

                async def refresh():
                    def check(reaction, user):
                        return user != self.client.user and str(reaction.emoji) == self.emoji and reaction.message.id == message.id
                    
                    try:
                        reaction, user = await self.client.wait_for('reaction_add', timeout=self.timeout, check=check)
                    except asyncio.TimeoutError:
                        await message.remove_reaction(self.emoji, self.client.user)
                        logging.info(self.emoji + ' reaction button timed out')
                        await self.action_timeout()
                    except asyncio.CancelledError:
                        logging.debug(self.emoji + ' canceled')
                        raise
                    else:
                        logging.debug(self.emoji + ' pressed')
                        self.coro[message] = asyncio.create_task(asyncio.coroutine(refresh)())
                        await self.action()
                
                self.coro[message] = asyncio.create_task(asyncio.coroutine(refresh)())
                # while self.coro[message]:
                #     await self.coro[message]
                #     self.coro[message] = asyncio.create_task(asyncio.coroutine(refresh)())
            else:
                logging.error('Registering button ' + self.emoji + 'failed. Message already registered.')
        else:
            logging.error('Registering button ' + self.emoji + 'failed. You must provide a discord Message object.')
    
    async def remove(self, message: discord.Message):
        if self.coro[message]:
            await message.remove_reaction(self.emoji, self.client.user)
            self.coro[message].cancel()
            del self.coro[message]
        else:
            logging.error('Button remove failed, message does not exist')

    async def remove_all(self, remove_reaction = True):
        for key in list(self.coro):
            if remove_reaction:
                await key.remove_reaction(self.emoji, self.client.user)
            self.coro[key].cancel()
            del self.coro[key]