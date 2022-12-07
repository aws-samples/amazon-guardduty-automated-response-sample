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
from typing import List, Dict, Any

from aws_lambda_powertools import Logger
import boto3
import botocore

from quarantine.constants import SSM_DRAIN_TIME_SECS, BOTO3_CONFIG
from quarantine.utils import get_prefix

BUCKET_NAME = os.environ["ARTIFACT_BUCKET"]
NOTIFICATION_TOPIC_ARN = os.environ["NOTIFICATION_TOPIC_ARN"]
SSM_ROLE_ARN = os.environ["SSM_ROLE_ARN"]
logger = Logger(child=True)

__all__ = ["SSM"]


class SSM:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("ssm", config=BOTO3_CONFIG)

    def describe_instance_information(self, instance_id: str) -> List[Dict[str, Any]]:
        """
        Describing instances managed by SSM
        """

        logger.info(f"Checking if instance {instance_id} managed by SSM")
        try:
            response = self.client.describe_instance_information(
                Filters=[{"Key": "InstanceIds", "Values": [instance_id]}]
            )
            logger.debug(f"Described SSM instance information for {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to describe SSM instance information for {instance_id}")
            raise

        return response.get("InstanceInformationList", [])

    def send_commands(self, instance_id: str, commands: List[str]) -> None:
        """
        Send commands through SSM to an instance
        """

        prefix = get_prefix(instance_id)

        params = {
            "InstanceIds": [instance_id],
            "DocumentName": "AWS-RunShellScript",
            "TimeoutSeconds": 240,
            "Parameters": {
                "commands": commands,
                "executionTimeout": ["3600"],
                "workingDirectory": ["/tmp"],
            },
            "OutputS3BucketName": BUCKET_NAME,
            "OutputS3KeyPrefix": f"{prefix}/ssm-output-file",
            "ServiceRoleArn": SSM_ROLE_ARN,
            "NotificationConfig": {
                "NotificationArn": NOTIFICATION_TOPIC_ARN,
                "NotificationEvents": [
                    "Success",
                    "TimedOut",
                    "Cancelled",
                    "Failed",
                ],
                "NotificationType": "Invocation",
            },
        }

        logger.info(f"Sending SSM commands to {instance_id}: {commands}")
        try:
            response = self.client.send_command(**params)
            logger.debug(f"Sent SSM commands to {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to send SSM commands to {instance_id}")
            raise

        command_id = response["Command"]["CommandId"]

        waiter = self.client.get_waiter("command_executed")
        try:
            # wait 60 seconds for all commands to execute
            waiter.wait(
                CommandId=command_id,
                InstanceId=instance_id,
                WaiterConfig={"Delay": 3, "MaxAttempts": 20},
            )
            logger.info(f"Waiting {SSM_DRAIN_TIME_SECS} seconds for SSM to complete uploads")
            time.sleep(SSM_DRAIN_TIME_SECS)
        except Exception:
            logger.exception("SSM commands were queued, but failed to execute before timeout")
