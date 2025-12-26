"""Debug command to check permissions."""

import discord
from discord import app_commands


@app_commands.command(
    name="debug-perms", description="Debug: Check your permissions in this channel"
)
async def debug_perms(interaction: discord.Interaction):
    """Show user's permissions in current channel."""

    if not interaction.guild or not interaction.channel:
        await interaction.response.send_message(
            "Must be in a guild channel", ephemeral=True
        )
        return

    member = interaction.guild.get_member(interaction.user.id)
    if not member:
        await interaction.response.send_message("Member not found", ephemeral=True)
        return

    permissions = interaction.channel.permissions_for(member)

    embed = discord.Embed(title="🔍 Permission Debug", color=discord.Color.blue())

    embed.add_field(name="Channel", value=f"#{interaction.channel.name}", inline=False)

    embed.add_field(
        name="Channel Name (lowercase)",
        value=interaction.channel.name.lower(),
        inline=False,
    )

    embed.add_field(
        name="Manage Channels",
        value="✅ Yes" if permissions.manage_channels else "❌ No",
        inline=True,
    )

    embed.add_field(
        name="Administrator",
        value="✅ Yes" if permissions.administrator else "❌ No",
        inline=True,
    )

    # Show all roles
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed.add_field(
        name="Your Roles", value=", ".join(roles) if roles else "None", inline=False
    )

    # Check team detection
    channel_name = interaction.channel.name.lower()
    team_mappings = {
        "engineering": "Engineering",
        "product": "Product",
        "business": "Business",
    }

    detected_team = None
    for keyword, team in team_mappings.items():
        if keyword in channel_name:
            detected_team = team
            break

    embed.add_field(
        name="Detected Team",
        value=detected_team if detected_team else "❌ No team detected",
        inline=False,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
