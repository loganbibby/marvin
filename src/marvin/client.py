import json
from datetime import datetime

import click

from .aws import client as aws
from .profiles import AWSSessionProfile, AWSKeyProfile


"""
Refresh your AWS MFA session with Marvin.

To run:
> python marvin.py standard

Expected setup of ~/.aws/credentials:
> [standard] <- You can change this
> region=us-east-2 <- optional, see -r/--region and [fetchmfa].region
>
> [fetchmfa]
> aws_access_key_id=[...]
> aws_secret_access_key=[...]
> mfa_serial=arn:aws:iam::XXX:mfa/<AWS USER ID>
> session_duration=129600 <- optional, see -t/--duration
> region=us-east-2 <- option, see -r/--region and [standard].region
"""


class Client(object):
    def __init__(self, **kwargs):
        self.key_profile = AWSKeyProfile(kwargs.get("key_profile"))
        self.session_profile = AWSSessionProfile(kwargs.get("session_profile") or f"{self.key_profile.name}_fetch")
        self.mfa_token = kwargs.get("mfa_token")
        self.debug = kwargs.get("debug") or False
        self.force = kwargs.get("force") or False
        self.session_duration = kwargs.get("duration") or 129600
        self.aws_region = kwargs.get("region")

    @property
    def session_name(self):
        return self.key_profile.name

    @property
    def is_refresh_needed(self):
        return self.key_profile.has_expired

    def prompt_for_mfa_token(self):
        self.mfa_token = click.prompt(
            click.style("Enter token from your authentication app", fg="cyan"),
            type=int
        )
    
    def update_session_token(self):
        response = aws.get_session_token(
            self.session_profile.name,
            self.mfa_token,
            self.session_duration,
            self.session_profile.mfa
        )

        if not response.is_success:
            return False

        credentials = response.value.get("Credentials")

        self.key_profile.access_key = credentials.get("AccessKeyId")
        self.key_profile.secret_key = credentials.get("SecretAccessKey")
        self.key_profile.session_token = credentials.get("SessionToken")
        self.key_profile.expires_on = self.key_profile.get_date(credentials.get("Expiration"))
        self.key_profile.dump()
        return True
