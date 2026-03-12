from discord.ext.commands import Bot, Context
from discord import Intents, ButtonStyle, Interaction, AuditLogAction, Embed, User, TextStyle, TextChannel
from discord.ui import View, Button, Modal, TextInput
from functools import partial
import datetime as dt
import dependencies as deps
from os import getenv
from dotenv import load_dotenv

bot = Bot(command_prefix="!", intents=Intents.all())
link = 'https://discord.gg/QFhN3mp597'

async def give_link(interaction2: Interaction):
    await interaction2.response.send_message(f'[Запрошенная вами ссылка на сервер Эдемия]({link})')

async def adm(interaction2: Interaction, user: User | None):
    modal = AnswerModal(user, False, guild_id=interaction2.guild_id)
    await interaction2.response.send_modal(modal=modal)

@bot.command(name='запустить_рассылку') 
async def run_mailing(ctx: Context):
    if not ctx.author.guild_permissions.administrator:
        return 
    
    async def callback(interaction: Interaction):
        if ctx.author.id != interaction.user.id:
            await interaction.response.send_message("Это не ваша кнопка!", ephemeral=True)
            return
        counter = 0
        await interaction.response.send_message('Начинаю рассылку')

        embed = Embed(
            title='Эдемия', 
            description='Здравствуйте! Наш сервер подвергся крашу и прямо сейчас идет восстановление. Оно уже почти закончено и стоит на финальном этапе. Если вы хотите вернуться на сервер нажмите на первую кнопку. Если вы хотите связаться с администрацией нажмите на вторую кнопку'
            )
        embed.set_footer(text=ctx.author.global_name, icon_url=ctx.author.avatar.url)
        async for auditlog in interaction.guild.audit_logs(
            action=AuditLogAction.ban, 
            before=dt.datetime(2026, 3, 12), 
            after=dt.datetime(2026, 3, 9, 23, 59, 59)
            ):
            try:
                await interaction.guild.unban(auditlog.target)
            except:
                pass

            try:
                view = View(timeout=None)
                button = Button(label='Да, я хочу получить ссылку') 
                send_msg = Button(label='Написать администрации')

                button.callback = give_link
                send_msg.callback = partial(adm, user=auditlog.target)

                view.add_item(button)
                view.add_item(send_msg)

                await auditlog.target.send(embed=embed, view=view)
                counter+= 1
            except:
                continue
        await interaction.followup.send(f'Рассылка завершена. Получили сообщение {counter} человек')
    
    view = View(timeout=None)
    button = Button(label='Подтверждаю', style=ButtonStyle.green) 

    button.callback = callback
    view.add_item(button)

    await ctx.reply('Подтвердите рассылку', view=view) 


class AnswerModal(Modal):
    def __init__(self, user: User, user_send: bool, guild_id: int = None):
        super().__init__(title='Написание сообщения', timeout=None)
        self.user = user
        self.user_send = user_send
        self.guild_id = guild_id

        self.content = TextInput(label='Содержание', style=TextStyle.paragraph, max_length=1024)

        self.add_item(self.content)
        
    async def on_submit(self, interaction: Interaction):
        embed = Embed(title='Ответ получен!', description=self.content.value)
        embed.set_footer(text=interaction.user.global_name, icon_url=interaction.user.avatar.url)

        if not self.user_send:
            async def callback(interaction2: Interaction):
                guild = bot.get_guild(self.guild_id)
                if not guild:
                    await interaction2.response.send_message('Не удалось найти сервер!', ephemeral=True)
                    return
                member = guild.get_member(interaction2.user.id)
                if not member or not member.guild_permissions.administrator:
                    await interaction2.response.send_message('Вы не имеете права использовать эту кнопку!', ephemeral=True)
                    return
                modal = AnswerModal(self.user, True, guild_id=self.guild_id)
                await interaction2.response.send_modal(modal=modal)

            view = View(timeout=None)
            button = Button(label='Ответить')

            button.callback = callback
            view.add_item(button)

            await deps.channel.send(embed=embed, view=view) 
        else:
            async def callback(interaction2: Interaction):
                modal = AnswerModal(self.user, False, guild_id=self.guild_id)
                await interaction2.response.send_modal(modal=modal)

            view = View(timeout=None)
            button = Button(label='Ответить')

            button.callback = callback
            view.add_item(button)

            await self.user.send(embed=embed, view=view) 
        await interaction.response.send_message('Сообщение отправлено! Прошу не переписывайтесь слишком много')




async def on_ready():
    deps.channel = (await (await bot.fetch_guild(1285154407083675699)).fetch_channel(1481243103255072770))

bot.add_listener(on_ready)

load_dotenv()
TOKEN = getenv('TOKEN')
bot.run(TOKEN)