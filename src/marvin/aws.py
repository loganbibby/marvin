import subprocess
import json
import re

import click

from .exceptions import *


error_response = re.compile(r"^An error occurred \((\w+)\) when calling the \w+ operation: (.+)$")


class AWSResponse(object):
    def __init__(self, cmd, cmd_group, output, is_json=True, cmd_name=None, cmd_opts=None, cmd_pmt=None):
        self.command = cmd
        self.command_group = cmd_group
        self.command_name = cmd_name
        self.command_options = cmd_opts
        self.command_parameters = cmd_pmt
        self.output = output

        self.value = self.output.stdout.strip()

        self.is_success = True
        self.error_text = None
        self.error_code = None

        error = error_response.match(self.value)

        if error:
            self.is_success = False
            self.error_text = error.group(2)
            self.error_code = error.group(1)
        elif is_json:
            if self.value.startswith("{") or self.value.startswith("["):
                self.value = json.loads(self.value)
            else:
                self.is_success = False
                self.error_text = self.value
                self.error_code = "invalid_json_response"


class AWSClient(object):
    CONFIGURE = "configure"
    STS = "sts"

    def __init__(self, debug=True):
        self.aws_cli = "aws"
        self.debug = debug

    def run_command(self, cmd_group, cmd_name=None, *args, **kwargs):
        cmd = [self.aws_cli, cmd_group]

        if cmd_name:
            cmd.append(cmd_name)

        if len(args):
            cmd += args

        for key, value in kwargs.items():
            key = key.replace("_", "-")
            cmd.append(f'--{key}="{value}"')

        cmd = " ".join(cmd)

        if self.debug:
            click.echo(f"Running command: {cmd}")

        output = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )

        response = AWSResponse(cmd=cmd, cmd_group=cmd_group, cmd_name=cmd_name, cmd_opts=args, cmd_pmt=kwargs,
                               output=output, is_json=kwargs.get("output") == "json")

        if self.debug:
            click.echo(f'Command output: "{response.value}"')

        return response

    def get_profile_value(self, profile, key):
        return self.run_command(self.CONFIGURE, "get", key, profile=profile).value

    def set_profile_value(self, profile, key, value):
        return self.run_command(self.CONFIGURE, "set", key, value, profile=profile).is_success

    def get_session_token(self, profile, token, duration, mfa_device):
        response = self.run_command(self.STS, "get-session-token", profile=profile, output="json",
                                    duration_seconds=duration, token_code=token, serial_number=mfa_device)

        if not response.is_success:
            if response.error_code == "AccessDenied" and "MultiFactorAuthentication failed" in response.error_text:
                raise InvalidToken()
            if "Invalid length for parameter TokenCode" in response.error_text:
                raise InvalidTokenLength(response.error_text[-2:].strip())

        return response


client = AWSClient()
