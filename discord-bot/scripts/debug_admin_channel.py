"""Debug script to check admin channel access and resend notification."""

import asyncio
import os
from uuid import UUID

import discord
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ADMIN_CHANNEL_ID = int(os.getenv("DISCORD_ADMIN_CHANNEL_ID"))
REQUEST_ID = UUID("0671059e-a9be-4e3c-a8b3-123ac2864077")

print("=" * 60)
print("Admin Channel Debug & Notification Resend")
print("=" * 60)
print()
print(f"Admin Channel ID: {ADMIN_CHANNEL_ID}")
print(f"Request ID: {REQUEST_ID}")
print()


async def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✅ Bot connected as {client.user}")
        print()

        # Check admin channel
        print("📋 Step 1: Checking admin channel access...")
        admin_channel = client.get_channel(ADMIN_CHANNEL_ID)

        if not admin_channel:
            print(f"❌ Could not find channel with ID {ADMIN_CHANNEL_ID}")
            print()
            print("Possible issues:")
            print("1. Channel ID is wrong")
            print("2. Bot is not in the server")
            print("3. Bot doesn't have access to the channel")
            print()
            print("Channels bot can see:")
            for guild in client.guilds:
                print(f"\n  Server: {guild.name}")
                for channel in guild.text_channels:
                    print(f"    - #{channel.name} (ID: {channel.id})")
            await client.close()
            return

        print(f"✅ Found channel: #{admin_channel.name}")
        print()

        # Check permissions
        print("📋 Step 2: Checking bot permissions...")
        permissions = admin_channel.permissions_for(admin_channel.guild.me)

        print(f"   - Send Messages: {permissions.send_messages}")
        print(f"   - Embed Links: {permissions.embed_links}")
        print(f"   - Attach Files: {permissions.attach_files}")
        print(f"   - Read Message History: {permissions.read_message_history}")

        if not permissions.send_messages:
            print()
            print("❌ Bot doesn't have permission to send messages in this channel!")
            print("   Fix: Give bot 'Send Messages' permission in channel settings")
            await client.close()
            return

        print()
        print("📋 Step 3: Getting pending request from database...")

        # Import data service
        import sys
        from pathlib import Path

        shared_services_path = Path.cwd().parent / "shared-services"
        data_service_path = shared_services_path / "data-service"
        sys.path.insert(0, str(data_service_path))

        from data_service import create_data_service

        data_service = create_data_service()
        pending = data_service.get_pending_onboarding(REQUEST_ID)

        if not pending:
            print(f"❌ Request {REQUEST_ID} not found")
            await client.close()
            return

        print(f"✅ Found request:")
        print(f"   Name: {pending.name}")
        print(f"   Email: {pending.email}")
        print(f"   Status: {pending.status}")
        print()

        if pending.status.value != "pending":
            print(f"⚠️  Request status is '{pending.status.value}', not 'pending'")
            print("   This request may have already been processed")
            await client.close()
            return

        # Get the Discord user
        print("📋 Step 4: Fetching Discord user...")
        try:
            discord_user = await client.fetch_user(pending.discord_id)
            print(f"✅ Found user: {discord_user.name} ({discord_user.id})")
        except Exception as e:
            print(f"❌ Could not fetch user: {e}")
            await client.close()
            return

        print()
        print("📋 Step 5: Sending admin notification...")

        # Create embed
        embed = discord.Embed(
            title="🆕 New Onboarding Request",
            description=f"**{discord_user.mention}** wants to join the team!",
            color=discord.Color.blue(),
        )

        embed.add_field(name="Discord User", value=str(discord_user), inline=False)
        embed.add_field(name="Name", value=pending.name, inline=True)
        embed.add_field(name="Email", value=pending.email, inline=True)

        if pending.phone:
            embed.add_field(name="Phone", value=pending.phone, inline=True)

        embed.add_field(name="Bio & Experience", value=pending.bio[:1024], inline=False)
        embed.set_thumbnail(url=discord_user.display_avatar.url)
        embed.set_footer(text=f"Request ID: {REQUEST_ID}")

        # Import services
        from bot.onboarding import ApprovalView
        from bot.services import DocsService, TeamMemberService

        team_service = TeamMemberService()
        docs_service = DocsService()

        # Create view with buttons
        view = ApprovalView(REQUEST_ID, pending.discord_id, team_service, docs_service)

        try:
            message = await admin_channel.send(embed=embed, view=view)
            print(f"✅ Admin notification sent successfully!")
            print(f"   Message ID: {message.id}")
            print(f"   Jump URL: {message.jump_url}")
        except Exception as e:
            print(f"❌ Failed to send message: {e}")

        print()
        print("=" * 60)
        print("Done! Check the admin channel now.")
        print("=" * 60)

        await client.close()

    await client.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
