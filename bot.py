import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from discord.errors import NotFound

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Variables globales
entrenador_online = None
participantes = []
prueba_en_curso = False
mensaje_prueba = None
canal_prueba_id = None


class PruebaView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Unirse a la cola",
                       style=discord.ButtonStyle.green,
                       custom_id="unirse_cola")
    async def unirse_cola(self, interaction: discord.Interaction,
                          button: Button):
        global participantes
        if interaction.user not in participantes:
            participantes.append(interaction.user)
            await actualizar_mensaje_prueba()
            await interaction.response.send_message("¡Te has unido a la cola!",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("Ya estás en la cola.",
                                                    ephemeral=True)


async def actualizar_mensaje_prueba():
    global mensaje_prueba, entrenador_online, participantes, prueba_en_curso
    if not canal_prueba_id:
        return

    canal = bot.get_channel(canal_prueba_id)
    if not canal:
        return

    embed = discord.Embed(title="Sistema de Pruebas de Ascenso")
    view = PruebaView() if (entrenador_online is not None
                            and not prueba_en_curso) else None

    if entrenador_online:
        embed.color = discord.Color.green()
        embed.description = f"Prueba abierta ✳️\n{entrenador_online.mention} está online"
        if participantes:
            embed.add_field(name="Participantes",
                            value="\n".join(
                                [user.mention for user in participantes]),
                            inline=False)
    else:
        embed.color = discord.Color.red()
        embed.description = "Prueba cerrada 🔴\nNo hay entrenadores online"
        embed.set_footer(
            text=f"Última sesión: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    try:
        if mensaje_prueba:
            await mensaje_prueba.edit(embed=embed, view=view)
        else:
            # Si no hay mensaje, crear uno nuevo
            mensaje_prueba = await canal.send(embed=embed, view=view)
    except (NotFound, AttributeError):
        # Si el mensaje fue eliminado o no se puede editar, crear uno nuevo
        mensaje_prueba = await canal.send(embed=embed, view=view)


@bot.command()
@commands.has_role("Entrenador")
async def set_here(ctx):
    global canal_prueba_id, mensaje_prueba
    canal_prueba_id = ctx.channel.id
    await actualizar_mensaje_prueba()
    await ctx.send("✅ Canal de pruebas configurado aquí.", delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def online(ctx):
    global entrenador_online, prueba_en_curso
    if entrenador_online:
        await ctx.send("⚠️ Ya hay un entrenador online.", delete_after=5)
        return
    entrenador_online = ctx.author
    prueba_en_curso = False
    await actualizar_mensaje_prueba()
    await ctx.send("🟢 Modo entrenador activado.", delete_after=5)
    await asyncio.sleep(7200)  # 2 horas de timeout
    if entrenador_online == ctx.author:
        await offline(ctx)


@bot.command()
@commands.has_role("Entrenador")
async def offline(ctx):
    global entrenador_online, participantes, prueba_en_curso
    entrenador_online = None
    participantes = []
    prueba_en_curso = False
    await actualizar_mensaje_prueba()
    await ctx.send("🔴 Modo entrenador desactivado.", delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def iniciar(ctx):
    global prueba_en_curso
    prueba_en_curso = True
    await actualizar_mensaje_prueba()
    await ctx.send(
        "🟢 Prueba iniciada. Los participantes no pueden unirse ahora.",
        delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def finalizar(ctx):
    global entrenador_online, participantes, prueba_en_curso
    prueba_en_curso = False
    participantes = []
    await actualizar_mensaje_prueba()
    await ctx.send("🔴 Prueba finalizada. Se reinició la cola.", delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def fix_msg(ctx):
    global mensaje_prueba
    mensaje_prueba = None
    await actualizar_mensaje_prueba()
    await ctx.send("✅ Mensaje recreado manualmente.", delete_after=5)


# Sistema keep_alive para 24/7
from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "Bot en línea"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


keep_alive()

bot.run(os.getenv('TOKEN'))  # Usa variable de entorno en Replit
# Si es local, reemplaza por: bot.run("TU_TOKEN")