import asyncio
import os
import click
from google import genai


@click.command()
def setup():
    """Interactive setup wizard for the Social Media Content Scheduler."""
    click.echo("=" * 60)
    click.echo("  Social Media Content Scheduler - Setup Wizard")
    click.echo("=" * 60)

    env_vars = {}

    # Gemini API Key
    click.echo("\n--- Gemini AI Configuration ---")
    gemini_key = click.prompt("Enter your Gemini API key")

    click.echo("Validating Gemini API key...")
    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'hello' in one word.",
        )
        click.echo(f"Gemini API key is valid! Response: {response.text.strip()}")
        env_vars["GEMINI_API_KEY"] = gemini_key
        env_vars["GEMINI_MODEL"] = "gemini-2.5-flash"
    except Exception as e:
        click.echo(f"Warning: Gemini API validation failed: {e}")
        if click.confirm("Save anyway?"):
            env_vars["GEMINI_API_KEY"] = gemini_key
            env_vars["GEMINI_MODEL"] = "gemini-2.5-flash"

    # Instagram
    if click.confirm("\nDo you want to configure Instagram?", default=True):
        from setup_wizard.instagram_setup import (
            print_instagram_guide,
            exchange_token,
            get_business_account_id,
        )

        print_instagram_guide()

        has_token = click.confirm("Do you already have a long-lived access token?")

        if has_token:
            token = click.prompt("Enter your Instagram long-lived access token")
            account_id = click.prompt("Enter your Instagram Business Account ID")
        else:
            app_id = click.prompt("Enter your Meta App ID")
            app_secret = click.prompt("Enter your Meta App Secret", hide_input=True)
            short_token = click.prompt("Enter your short-lived access token from Graph API Explorer")

            click.echo("Exchanging for long-lived token...")
            try:
                token = asyncio.run(exchange_token(app_id, app_secret, short_token))
                click.echo("Long-lived token obtained!")

                click.echo("Getting Instagram Business Account ID...")
                account_id = asyncio.run(get_business_account_id(token))
                click.echo(f"Business Account ID: {account_id}")
            except Exception as e:
                click.echo(f"Error: {e}")
                token = click.prompt("Enter token manually (or 'skip')", default="skip")
                account_id = click.prompt("Enter account ID manually (or 'skip')", default="skip")

        if token != "skip" and account_id != "skip":
            env_vars["INSTAGRAM_ACCESS_TOKEN"] = token
            env_vars["INSTAGRAM_BUSINESS_ACCOUNT_ID"] = account_id
            click.echo("Instagram configured!")

    # YouTube
    if click.confirm("\nDo you want to configure YouTube?", default=True):
        from setup_wizard.youtube_setup import print_youtube_guide, run_oauth_flow

        print_youtube_guide()

        secrets_file = click.prompt(
            "Path to client_secrets.json", default="client_secrets.json"
        )
        token_file = click.prompt(
            "Path to save OAuth token", default="youtube_token.json"
        )

        env_vars["YOUTUBE_CLIENT_SECRETS_FILE"] = secrets_file
        env_vars["YOUTUBE_OAUTH_TOKEN_FILE"] = token_file

        if os.path.exists(secrets_file):
            if click.confirm("Run OAuth flow now?", default=True):
                success = run_oauth_flow(secrets_file, token_file)
                if success:
                    click.echo("YouTube configured!")
                else:
                    click.echo("YouTube OAuth flow failed. You can retry later.")
        else:
            click.echo(f"Note: {secrets_file} not found. Place it and re-run the wizard.")

    # Timezone
    timezone = click.prompt("\nTimezone", default="UTC")
    env_vars["TIMEZONE"] = timezone
    env_vars["DATABASE_URL"] = "sqlite:///./social_media_agent.db"
    env_vars["LOG_LEVEL"] = "INFO"

    # Write .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    click.echo(f"\nConfiguration saved to {env_path}")
    click.echo("\nSetup complete! Start the server with: python run.py")
    click.echo("API docs will be at: http://localhost:8000/docs")


if __name__ == "__main__":
    setup()
