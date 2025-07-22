import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timezone
from discord.errors import NotFound

# Configuración de intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Estructura para manejar múltiples grupos
grupos = {}

class GrupoPrueba:
    def __init__(self):
        self.entrenador = None
        self.participantes = []
        self.activo = False
        self.mensaje = None
        self.canal_id = None
        self.ultima_actividad = None

class VistaPrueba(View):
    def __init__(self, grupo_id):
        super().__init__(timeout=None)
        self.grupo_id = grupo_id

    @discord.ui.button(label="Unirse", style=discord.ButtonStyle.green, custom_id="unirse_cola")
    async def unirse(self, interaction, button):
        grupo = grupos.get(self.grupo_id)
        if not grupo:
            return

        if interaction.user not in grupo.participantes:
            grupo.participantes.append(interaction.user)
            await actualizar_mensaje_grupo(self.grupo_id)
            await interaction.response.send_message("✅ Te has unido correctamente", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Ya estás en la cola", ephemeral=True)

async def actualizar_mensaje_grupo(grupo_id):
    grupo = grupos.get(grupo_id)
    if not grupo or not grupo.canal_id:
        return

    canal = bot.get_channel(grupo.canal_id)
    if not canal:
        return

    # Formato de hora dinámico para Discord
    timestamp = grupo.ultima_actividad or int(datetime.now(timezone.utc).timestamp())
    hora_formato = f"<t:{timestamp}:F> (<t:{timestamp}:R>)"

    embed = discord.Embed(title=f"⚔️ Pruebas de Ascenso (Grupo {grupo_id})")
    
    if grupo.entrenador:
        embed.color = discord.Color.green()
        embed.description = f"**PRUEBA ABIERTA**\nEntrenador: {grupo.entrenador.mention}"
        if grupo.participantes:
            embed.add_field(name="Participantes", value="\n".join([u.mention for u in grupo.participantes]), inline=False)
    else:
        embed.color = discord.Color.red()
        embed.description = "**PRUEBA CERRADA**\nEsperando entrenadores..."
    
    embed.set_footer(text=f"Última actividad: {hora_formato}")
    vista = VistaPrueba(grupo_id) if grupo.entrenador and not grupo.activo else None

    try:
        if grupo.mensaje:
            await grupo.mensaje.edit(embed=embed, view=vista)
        else:
            grupo.mensaje = await canal.send(embed=embed, view=vista)
    except:
        grupo.mensaje = await canal.send(embed=embed, view=vista)

def crear_comandos_grupo(numero):
    @bot.command(name=f"set_here{numero}")
    @commands.has_role("Entrenador")
    async def set_here(ctx):
        if numero not in grupos:
            grupos[numero] = GrupoPrueba()
        grupos[numero].canal_id = ctx.channel.id
        grupos[numero].ultima_actividad = int(datetime.now(timezone.utc).timestamp()
        await actualizar_mensaje_grupo(numero)
        await ctx.send(f"✅ Canal configurado para Grupo {numero}", delete_after=5)

    @bot.command(name=f"online{numero}")
    @commands.has_role("Entrenador")
    async def online(ctx):
        grupo = grupos.get(numero)
        if not grupo:
            await ctx.send(f"⚠️ Primero usa `!set_here{numero}` en este canal", delete_after=5)
            return
        
        grupo.entrenador = ctx.author
        grupo.ultima_actividad = int(datetime.now(timezone.utc).timestamp())
        grupo.activo = False
        await actualizar_mensaje_grupo(numero)
        await ctx.send(f"🟢 Entrenador del Grupo {numero} ahora online", delete_after=5)

    @bot.command(name=f"offline{numero}")
    @commands.has_role("Entrenador")
    async def offline(ctx):
        grupo = grupos.get(numero)
        if not grupo:
            return
        
        grupo.entrenador = None
        grupo.participantes = []
        grupo.activo = False
        grupo.ultima_actividad = int(datetime.now(timezone.utc).timestamp())
        await actualizar_mensaje_grupo(numero)
        await ctx.send(f"🔴 Entrenador del Grupo {numero} ahora offline", delete_after=5)

    @bot.command(name=f"iniciar{numero}")
    @commands.has_role("Entrenador")
    async def iniciar(ctx):
        grupo = grupos.get(numero)
        if not grupo:
            return
        
        grupo.activo = True
        grupo.ultima_actividad = int(datetime.now(timezone.utc).timestamp())
        await actualizar_mensaje_grupo(numero)
        await ctx.send(f"⏳ Prueba del Grupo {numero} iniciada", delete_after=5)

    @bot.command(name=f"finalizar{numero}")
    @commands.has_role("Entrenador")
    async def finalizar(ctx):
        grupo = grupos.get(numero)
        if not grupo:
            return
        
        grupo.entrenador = None
        grupo.participantes = []
        grupo.activo = False
        grupo.ultima_actividad = int(datetime.now(timezone.utc).timestamp())
        await actualizar_mensaje_grupo(numero)
        await ctx.send(f"🏁 Prueba del Grupo {numero} finalizada", delete_after=5)

    @bot.command(name=f"reset{numero}")
    @commands.has_role("Entrenador")
    async def reset(ctx):
        grupos[numero] = GrupoPrueba()
        await ctx.send(f"🔄 Grupo {numero} reiniciado completamente", delete_after=5)

# Crear comandos para los grupos 1 al 10
for i in range(1, 11):
    crear_comandos_grupo(i)

# Sistema keep-alive
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# Manejo de errores al iniciar
try:
    bot.run(os.getenv('TOKEN'))
except Exception as e:
    print(f"❌ Error al iniciar el bot: {e}")
    raise