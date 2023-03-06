# Marvin, the AWS MFA helper bot

Marvin is a Python CLI for refreshing and checking your AWS sessions that require MFA. 

## Installation

_Note: Marvin relies on the `aws` CLI to be installed and accessible from PATH._

1. Clone this repo and go into the directory
2. Create a virtual environment (`python -m venv .venv`) and activate (`source .venv/bin/activate` or `.venv\Scripts\activate` on Windows)
3. Install requirements (`pip install -r requirements.txt`)

## AWS Credentials File

For each of the profiles you want to manage with Marvin, it must be already setup in `~/.aws/credentials`. Each profile requires two profiles in that file: the session profile and key profile.

The key profile requires the following settings: `aws_access_key_id`, `aws_secret_access_key`, and `mfa_serial` (your MFA device ARN).

The session profile is named based on the key profile's name followed by `_fetch` -- so a key profile called `default` would have a session profile called `default_fetch`. 

Expirations and other data is saved in `~/.aws/config`.

## Commands

All commands run from `src/run.py` and can be invoked using `python src/run.py <command>` or `src/run.py` if the file has executable permission. 

### `check`
Check a profile's expiration.

Required argument: `key_profile`

Optional parameter: `--session-profile`

### `refresh`
Refresh a session's token. 

Required argument: `key_profile`

Optional parameters: `--session-profile`, `--duration` (in seconds, defaults to 36 hours), and `--token` (an MFA token).

## To-Do

* Better integration with `aws`
* Ability to list profiles
* Check status of all profiles

## Version

* `0.1` - Initial release
