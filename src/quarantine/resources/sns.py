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

from aws_lambda_powertools import Logger
import boto3
import botocore

from quarantine.utils import json_dumps

TOPIC_ARN = os.environ["NOTIFICATION_TOPIC_ARN"]

logger = Logger(child=True)

__all__ = ["SNS"]


class SNS:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("sns")

    def publish(self, instance_id: str, message: str) -> None:
        params = {
            "TopicArn": TOPIC_ARN,
            "Message": json_dumps({"default": message, "instance_id": instance_id}),
            "MessageStructure": "json",
            "MessageAttributes": {"InstanceId": {"DataType": "String", "StringValue": instance_id}},
        }
        logger.debug(params)

        logger.debug(f"Publishing message to topic {TOPIC_ARN}")
        try:
            self.client.publish(**params)
            logger.debug(f"Published message to topic {TOPIC_ARN}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to publish message to topic {TOPIC_ARN}")
