import json
import subprocess
import argparse
from textwrap import wrap
from datetime import datetime


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


class Marvin(object):
    DEBUG = False
    DATEFMT = '%Y-%m-%dT%H:%M:%SZ'
    CONFIG_MAP = {
        'session': [
            'session_token_duration',
            'mfa_serial',
        ],
        'key': [
            'aws_secret_access_key',
            'aws_session_token',
            'aws_access_key_id',
            'expiration',
        ]
    }
    
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('profile')
        parser.add_argument(
            '-s', '--session-profile',
            default='fetchmfa',
            help="Session profile name from .aws/credentials (default: fetchmfa)"
        )
        parser.add_argument(
            '-t', '--mfa-token',
            help="MFA token to use (otherwise, you will be prompted)"
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help="Shows additional debug information"
        )
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help="Forces a session refresh even if it hasn't expired"
        )
        parser.add_argument(
            '-d', '--duration',
            type=int,
            default=129600,
            help="Sets the session duration in seconds (defaults to 129,600 or 36 hours)"
        )
        parser.add_argument(
            '-r', '--region',
            help="Sets the session's region and can be set in either the session or key profile with session taking priority."
        )

        self.args = parser.parse_args()
        
        self.DEBUG = self.args.debug
        
        self.profiles = {
            'key': self.args.profile,
            'session': self.args.session_profile
        }
    
    def __call__(self):
        self.show_marvin()
        print("")
        
        self.show_welcome()
        print("")
                
        if not self.is_refresh_needed and not self.args.force:
            print('Refresh is not needed')
            return
           
        if self.DEBUG:
            print('Refresh is needed')
        
        self.fetch()
    
    def print(self, msg, width=60, post_n=0):
        if isinstance(msg, list):
            msg = "\n".join(msg)
        
        split = msg.split("\n")
        msg = ""
        
        for m in split:
            msg += "\n".join(wrap(m, width=width)) + "\n"
        
        msg = msg[:-1]
        
        for i in range(0, post_n):
            msg += "\n"
        
        print(msg)
    
    def show_marvin(self):
        s = []
        s.append(" __   __ _______ ______   __   __ ___ __    _ ")
        s.append("|  |_|  |   _   |    _ | |  | |  |   |  |  | |")
        s.append("|       |  |_|  |   | || |  |_|  |   |   |_| |")
        s.append("|       |       |   |_||_|       |   |       |")
        s.append("|       |       |    __  |       |   |  _    |")
        s.append("| ||_|| |   _   |   |  | ||     ||   | | |   |")
        s.append("|_|   |_|__| |__|___|  |_| |___| |___|_|  |__|")
        
        self.print(s, post_n=1)
    
    def show_welcome(self):
        self.print("Hello! My name is Marvin and I'll handle your AWS multi-factor authentication session for AWS CLI.", post_n=1)
        
        settings = {
            "Profile": self.args.profile,
            "Duration (-d)": "{} seconds or {} hours".format(self.args.duration, self.args.duration / 60 / 60),
            "Session Profile (-s)": self.args.session_profile,
            "Session refresh will be forced (-f)": self.args.force,
            "Debug mode is ENABLED": self.args.debug
        }
        
        self.print([" * {}{}".format(k, "" if not isinstance(v, str) else ": {}".format(v)) for k, v in settings.items() if v], post_n=1)
        
    def _config(self, profile, action, key, value=None):
        cmd = 'aws configure {} {} '.format(action, key)
        
        if action == 'set':
            cmd += '{} '.format(value)
        
        cmd += '--profile {}'.format(profile)
        
        return self.run_command(cmd)
    
    def get_config(self, key):
        return self._config(
            self.get_profile_for_config(key),
            'get',
            key
        )
    
    def set_config(self, key, value):
        self._config(
            self.get_profile_for_config(key),
            'set',
            key,
            value
        )
    
    def get_profile_for_config(self, key):
        profile = None
        
        for profile_name, keys in self.CONFIG_MAP.items():
            if key not in keys:
                continue
            
            profile = profile_name
            break
        
        if not profile:
            raise KeyError('Could not find correct profile for "{}"'.format(key))
        
        profile = self.profiles[profile]
        
        if self.DEBUG:
            print('Profile for "{}" is "{}"'.format(key, profile))
        
        return profile
    
    def run_command(self, cmd):
        if self.DEBUG:
            print('Running command: {}'.format(cmd))
        
        o = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        
        output = o.stdout.rstrip()
        
        if self.DEBUG:
            print('Output: "{}"'.format(output))
        
        return output
    
    @property
    def is_refresh_needed(self):
        expiration = self.get_config('expiration')
        
        try:
            expiration = datetime.strptime(expiration, self.DATEFMT)
            
            if expiration > datetime.utcnow():
                self.print('Current session expires on {} UTC'.format(expiration.strftime('%m/%d/%Y %H:%M')), post_n=1)
                return False
            
        except ValueError:
            if self.DEBUG:
                print('Unable to convert to datetime: "{}"'.format(expiration))
        
        return True
    
    def get_mfa_token(self):
        if self.args.mfa_token:
            return self.args.mfa_token 
        
        while True:
            mfa_token = input('Enter the MFA token from your authentication app: ').strip()
            print("")
            
            if not mfa_token:
                self.print('No MFA token was entered.')
            else:
                return mfa_token
    
    def fetch(self):
        """
        Fetches the session token
        
        Expected output of command:
            [
                "<ACCEES SECRET>",
                "<TOKEN>",
                "<EXPIRATION>",
                "<ACCESS KEY>"
            ]
        """
        
        data = {
            'mfa_token': self.get_mfa_token(),
            'session_profile': self.profiles['session'],
            'duration': self.get_config('session_token_duration') or self.args.duration,
            'mfa_serial': self.get_config('mfa_serial')
        }
        
        for key, value in data.items():
            if value:
                continue
            
            self.print('Missing data for session call: {}'.format(key))
            self.print("Cannot continue")
            return
        
        cmd = "aws sts get-session-token --profile {} --output json --duration-seconds {} --token-code {} --serial-number {} ".format(
            data['session_profile'],
            data['duration'],
            data['mfa_token'],
            data['mfa_serial']
        )
        
        if self.debug:
            self.print('Running command: {}'.format(cmd))
        
        response = self.run_command(cmd)
        
        if response == '':
            self.print('Something went wrong and AWS returned nothing :(')
            return
        
        if not response.startswith('{'):
            self.print('Unable to generate session token:')
            self.print(response)
            return
        
        response = json.loads(response)['Credentials']
        
        expiration = datetime.strptime(response['Expiration'], self.DATEFMT)
        
        self.print('Session token refreshed and will expire on {} UTC'.format(expiration.strftime('%m/%d/%Y %H:%M:%S')), post_n=1)
        
        self.set_config('aws_secret_access_key', response['SecretAccessKey'])
        self.set_config('aws_session_token', response['SessionToken'])
        self.set_config('aws_access_key_id', response['AccessKeyId'])
        self.set_config('expiration', expiration.strftime(self.DATEFMT))
        

if __name__ == '__main__':
    marvin = Marvin()
    marvin()
