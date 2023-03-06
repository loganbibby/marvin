import click

from .client import Client
from .aws import client as aws
from .exceptions import *


banner = """
 __   __ _______ ______   __   __ ___ __    _ 
|  |_|  |   _   |    _ | |  | |  |   |  |  | |
|       |  |_|  |   | || |  |_|  |   |   |_| |
|       |       |   |_||_|       |   |       |
|       |       |    __  |       |   |  _    |
| ||_|| |   _   |   |  | ||     ||   | | |   |
|_|   |_|__| |__|___|  |_| |___| |___|_|  |__|
"""


@click.group
@click.option("-d", "--debug", is_flag=True)
def cli(debug):
    click.secho(banner, fg="magenta")
    click.secho(
        "Hello! My name is Marvin and I'll handle your\nAWS multi-factor authentication session for AWS CLI.",
        fg="magenta"
    )
    click.echo("")

    aws.debug = debug


@cli.command()
@click.argument("key_profile")
@click.option("--session-profile", default=None)
@click.option("--token")
@click.option("--duration", type=int)
def refresh(**kwargs):
    client = Client(**kwargs)

    if client.is_refresh_needed and not client.mfa_token:
        client.prompt_for_mfa_token()

    while True:
        try:
            click.echo("")
            if client.update_session_token():
                click.secho(f"Your session information for {client.key_profile.name} has been updated!", fg="green")
                click.secho(f"The session will expire in {client.key_profile.expires_in_hours} hours", fg="green")
            else:
                click.secho("Unable to refresh your session", fg="red")
            break
        except InvalidToken as e:
            click.secho(str(e), fg="red")
            click.echo("")
            client.prompt_for_mfa_token()


@cli.command()
@click.argument("key_profile")
@click.option("--session-profile", default=None)
def check(**kwargs):
    client = Client(**kwargs)

    if client.is_refresh_needed:
        click.secho(f"Your {client.session_name} session is active and will expire in "
                    f"{client.key_profile.expires_in_hours} hours",
                    fg="green")
    else:
        click.secho(f"Your {client.session_name} session expired {abs(client.key_profile.expires_in_hours)} hours ago "
                    f"and needs to be refreshed.", fg="red")
