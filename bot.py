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

# Diccionarios para manejar múltiples instancias
entrenadores_online = {i: None for i in range(1, 11)}
participantes = {i: [] for i in range(1, 11)}
pruebas_en_curso = {i: False for i in range(1, 11)}
mensajes_prueba = {i: None for i in range(1, 11)}
canales_prueba = {i: None for i in range(1, 11)}


class PruebaView(View):
    def __init__(self, numero):
        super().__init__(timeout=None)
        self.numero = numero

    @discord.ui.button(label="Unirse a la cola",
                      style=discord.ButtonStyle.green,
                      custom_id="unirse_cola")
    async def unirse_cola(self, interaction: discord.Interaction, button: Button):
        if interaction.user not in participantes[self.numero]:
            participantes[self.numero].append(interaction.user)
            await actualizar_mensaje_prueba(self.numero)
            await interaction.response.send_message("¡Te has unido a la cola!", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estás en la cola.", ephemeral=True)


async def actualizar_mensaje_prueba(numero):
    canal = canales_prueba[numero]
    if not canal:
        return

    channel = bot.get_channel(canal)
    if not channel:
        return

    embed = discord.Embed(title=f"Sistema de Pruebas de Ascenso #{numero}")
    view = PruebaView(numero) if (entrenadores_online[numero] is not None and not pruebas_en_curso[numero]) else None

    if entrenadores_online[numero]:
        embed.color = discord.Color.green()
        embed.description = f"Prueba abierta ✳️\n{entrenadores_online[numero].mention} está online"
        if participantes[numero]:
            embed.add_field(name="Participantes",
                          value="\n".join([user.mention for user in participantes[numero]]),
                          inline=False)
    else:
        embed.color = discord.Color.red()
        embed.description = "Prueba cerrada 🔴\nNo hay entrenadores online"
        embed.set_footer(text=f"Última sesión: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    try:
        if mensajes_prueba[numero]:
            await mensajes_prueba[numero].edit(embed=embed, view=view)
        else:
            mensajes_prueba[numero] = await channel.send(embed=embed, view=view)
    except (NotFound, AttributeError):
        mensajes_prueba[numero] = await channel.send(embed=embed, view=view)


@bot.command()
@commands.has_role("Entrenador")
async def set_here1(ctx): await set_here(ctx, 1)
@bot.command()
@commands.has_role("Entrenador")
async def set_here2(ctx): await set_here(ctx, 2)
@bot.command()
@commands.has_role("Entrenador")
async def set_here3(ctx): await set_here(ctx, 3)
@bot.command()
@commands.has_role("Entrenador")
async def set_here4(ctx): await set_here(ctx, 4)
@bot.command()
@commands.has_role("Entrenador")
async def set_here5(ctx): await set_here(ctx, 5)
@bot.command()
@commands.has_role("Entrenador")
async def set_here6(ctx): await set_here(ctx, 6)
@bot.command()
@commands.has_role("Entrenador")
async def set_here7(ctx): await set_here(ctx, 7)
@bot.command()
@commands.has_role("Entrenador")
async def set_here8(ctx): await set_here(ctx, 8)
@bot.command()
@commands.has_role("Entrenador")
async def set_here9(ctx): await set_here(ctx, 9)
@bot.command()
@commands.has_role("Entrenador")
async def set_here10(ctx): await set_here(ctx, 10)

async def set_here(ctx, numero):
    canales_prueba[numero] = ctx.channel.id
    await actualizar_mensaje_prueba(numero)
    await ctx.send(f"✅ Canal de pruebas #{numero} configurado aquí.", delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def online1(ctx): await online(ctx, 1)
@bot.command()
@commands.has_role("Entrenador")
async def online2(ctx): await online(ctx, 2)
@bot.command()
@commands.has_role("Entrenador")
async def online3(ctx): await online(ctx, 3)
@bot.command()
@commands.has_role("Entrenador")
async def online4(ctx): await online(ctx, 4)
@bot.command()
@commands.has_role("Entrenador")
async def online5(ctx): await online(ctx, 5)
@bot.command()
@commands.has_role("Entrenador")
async def online6(ctx): await online(ctx, 6)
@bot.command()
@commands.has_role("Entrenador")
async def online7(ctx): await online(ctx, 7)
@bot.command()
@commands.has_role("Entrenador")
async def online8(ctx): await online(ctx, 8)
@bot.command()
@commands.has_role("Entrenador")
async def online9(ctx): await online(ctx, 9)
@bot.command()
@commands.has_role("Entrenador")
async def online10(ctx): await online(ctx, 10)

async def online(ctx, numero):
    if entrenadores_online[numero]:
        await ctx.send(f"⚠️ Ya hay un entrenador online en la prueba #{numero}.", delete_after=5)
        return
    entrenadores_online[numero] = ctx.author
    pruebas_en_curso[numero] = False
    await actualizar_mensaje_prueba(numero)
    await ctx.send(f"🟢 Modo entrenador #{numero} activado.", delete_after=5)
    await asyncio.sleep(7200)
    if entrenadores_online[numero] == ctx.author:
        await offline(ctx, numero)


@bot.command()
@commands.has_role("Entrenador")
async def offline1(ctx): await offline(ctx, 1)
@bot.command()
@commands.has_role("Entrenador")
async def offline2(ctx): await offline(ctx, 2)
@bot.command()
@commands.has_role("Entrenador")
async def offline3(ctx): await offline(ctx, 3)
@bot.command()
@commands.has_role("Entrenador")
async def offline4(ctx): await offline(ctx, 4)
@bot.command()
@commands.has_role("Entrenador")
async def offline5(ctx): await offline(ctx, 5)
@bot.command()
@commands.has_role("Entrenador")
async def offline6(ctx): await offline(ctx, 6)
@bot.command()
@commands.has_role("Entrenador")
async def offline7(ctx): await offline(ctx, 7)
@bot.command()
@commands.has_role("Entrenador")
async def offline8(ctx): await offline(ctx, 8)
@bot.command()
@commands.has_role("Entrenador")
async def offline9(ctx): await offline(ctx, 9)
@bot.command()
@commands.has_role("Entrenador")
async def offline10(ctx): await offline(ctx, 10)

async def offline(ctx, numero):
    entrenadores_online[numero] = None
    participantes[numero] = []
    pruebas_en_curso[numero] = False
    await actualizar_mensaje_prueba(numero)
    await ctx.send(f"🔴 Modo entrenador #{numero} desactivado.", delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def iniciar1(ctx): await iniciar(ctx, 1)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar2(ctx): await iniciar(ctx, 2)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar3(ctx): await iniciar(ctx, 3)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar4(ctx): await iniciar(ctx, 4)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar5(ctx): await iniciar(ctx, 5)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar6(ctx): await iniciar(ctx, 6)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar7(ctx): await iniciar(ctx, 7)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar8(ctx): await iniciar(ctx, 8)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar9(ctx): await iniciar(ctx, 9)
@bot.command()
@commands.has_role("Entrenador")
async def iniciar10(ctx): await iniciar(ctx, 10)

async def iniciar(ctx, numero):
    pruebas_en_curso[numero] = True
    await actualizar_mensaje_prueba(numero)
    await ctx.send(f"🟢 Prueba #{numero} iniciada. Los participantes no pueden unirse ahora.", delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def finalizar1(ctx): await finalizar(ctx, 1)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar2(ctx): await finalizar(ctx, 2)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar3(ctx): await finalizar(ctx, 3)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar4(ctx): await finalizar(ctx, 4)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar5(ctx): await finalizar(ctx, 5)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar6(ctx): await finalizar(ctx, 6)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar7(ctx): await finalizar(ctx, 7)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar8(ctx): await finalizar(ctx, 8)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar9(ctx): await finalizar(ctx, 9)
@bot.command()
@commands.has_role("Entrenador")
async def finalizar10(ctx): await finalizar(ctx, 10)

async def finalizar(ctx, numero):
    entrenadores_online[numero] = None  # Cambio clave: establecer entrenador como offline
    participantes[numero] = []
    pruebas_en_curso[numero] = False
    await actualizar_mensaje_prueba(numero)  # Esto hará que el embed vuelva al estado inicial
    await ctx.send(f"🔴 Prueba #{numero} finalizada. Sistema reiniciado completamente.", delete_after=5)


@bot.command()
@commands.has_role("Entrenador")
async def fix_msg1(ctx): await fix_msg(ctx, 1)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg2(ctx): await fix_msg(ctx, 2)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg3(ctx): await fix_msg(ctx, 3)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg4(ctx): await fix_msg(ctx, 4)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg5(ctx): await fix_msg(ctx, 5)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg6(ctx): await fix_msg(ctx, 6)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg7(ctx): await fix_msg(ctx, 7)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg8(ctx): await fix_msg(ctx, 8)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg9(ctx): await fix_msg(ctx, 9)
@bot.command()
@commands.has_role("Entrenador")
async def fix_msg10(ctx): await fix_msg(ctx, 10)

async def fix_msg(ctx, numero):
    mensajes_prueba[numero] = None
    await actualizar_mensaje_prueba(numero)
    await ctx.send(f"✅ Mensaje #{numero} recreado manualmente.", delete_after=5)


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

bot.run(os.getenv('TOKEN'))
