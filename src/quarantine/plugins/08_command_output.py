#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
* SPDX-License-Identifier: MIT-0
*
* Permission is hereby granted, free of charge, to any person obtaining a copy of this
* software and associated documentation files (the "Software"), to deal in the Software
* without restriction, including without limitation the rights to use, copy, modify,
* merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
* INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
* PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
* HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
* OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import time
from typing import Optional

from aws_lambda_powertools import Logger

from quarantine.plugins.abstract_plugin import AbstractPlugin
from quarantine.constants import SSM_COMMANDS

logger = Logger(child=True)
EC2_INSTANCE_PROFILE_ARN = os.getenv("EC2_INSTANCE_PROFILE_ARN")


class CommandOutput(AbstractPlugin):
    """
    Run commands from SSM and upload results to S3
    """

    def execute(self) -> Optional[str]:
        if not SSM_COMMANDS:
            logger.debug(f"No commands to execute on {self.instance_id}, skipping")
            return

        is_ssm_managed = len(self.ssm.describe_instance_information(self.instance_id)) > 0

        try:
            # remove any existing EC2 instance profiles
            self.ec2.remove_ec2_instance_profile(self.instance_id)
        except Exception:
            logger.exception(f"Unable to remove EC2 instance profile from {self.instance_id}")
            return

        if not is_ssm_managed:
            message = (
                f"Instance {self.instance_id} was not managed by SSM, skipping command capture"
            )
            logger.debug(message)
            return message

        if not EC2_INSTANCE_PROFILE_ARN:
            logger.warning("EC2_INSTANCE_PROFILE_ARN is not defined, unable to issue commands")
            return

        try:
            # attach limited EC2 instance profile
            self.ec2.attach_ec2_instance_profile(self.instance_id, EC2_INSTANCE_PROFILE_ARN)

            # wait 5 seconds for the instance profile to stabilize
            time.sleep(5)

            self.ssm.send_commands(self.instance_id, SSM_COMMANDS)

            # remove the limited EC2 instance profiles
            self.ec2.remove_ec2_instance_profile(self.instance_id)

            message = f"Captured output from {self.instance_id} for commands: {SSM_COMMANDS}"
        except Exception:
            message = (
                f"Unable to capture output from {self.instance_id} for commands: {SSM_COMMANDS}"
            )
            logger.exception(message)

        return message
