from datetime import datetime

from .aws import client as aws


date_format = '%Y-%m-%dT%H:%M:%SZ'


class AWSProfile(object):
    mapping = {}

    def __init__(self, profile_name):
        self.name = profile_name
        self.load()

    def load(self):
        for attr_name, profile_name in self.mapping.items():
            value = aws.get_profile_value(self.name, profile_name)

            method = f"get_{attr_name}_value"
            if hasattr(self, method):
                value = getattr(self, method)(value)

            setattr(self, attr_name, value)

    def dump(self):
        for attr_name, profile_name in self.mapping.items():
            value = getattr(self, attr_name)

            method = f"set_{attr_name}_value"
            if hasattr(self, method):
                value = getattr(self, method)(value)

            if value is None:
                continue

            if not aws.set_profile_value(self.name, profile_name, value):
                raise Exception("unable to save to profile")

    def get_date(self, value):
        if not value:
            return value
        return datetime.strptime(value, date_format)

    def set_date(self, value):
        if not value:
            return value
        return value.strftime(date_format)


class AWSSessionProfile(AWSProfile):
    mapping = {
        "access_key": "aws_access_key_id",
        "access_secret": "aws_secret_access_key",
        "duration": "session_token_duration",
        "mfa": "mfa_serial",
        "region": "region",
    }


class AWSKeyProfile(AWSProfile):
    mapping = {
        "access_key": "aws_access_key_id",
        "access_secret": "aws_secret_access_key",
        "session_token": "aws_session_token",
        "expires_on": "expiration",
        "region": "region",
    }

    def get_expires_on_value(self, value):
        return self.get_date(value)

    def set_expires_on_value(self, value):
        return self.set_date(value)

    @property
    def has_expired(self):
        return self.expires_on < datetime.utcnow()

    @property
    def expires_in_seconds(self):
        return (self.expires_on - datetime.utcnow()).total_seconds()

    @property
    def expires_in_hours(self):
        return round(self.expires_in_seconds / 60 / 60, 1)
