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

from aws_lambda_powertools import Logger
import boto3
import botocore

logger = Logger(child=True)

__all__ = ["AutoScaling"]


class AutoScaling:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("autoscaling")

    def detach_instance(self, instance_id: str) -> None:
        """
        Detach an instance from any autoscaling groups
        """

        logger.info(f"Checking if instance {instance_id} is attached to autoscaling groups")
        try:
            response = self.client.describe_auto_scaling_instances(InstanceIds=[instance_id])
            logger.debug("Described auto scaling instances")
        except botocore.exceptions.ClientError:
            logger.exception("Failed to describe auto scaling instances")
            raise

        instances = response.get("AutoScalingInstances", [])
        if not instances:
            logger.info(f"Instance {instance_id} not attached to any auto scaling groups")
            return

        for instance in instances:
            asg_name = instance["AutoScalingGroupName"]
            logger.info(f"Detaching {instance_id} from {asg_name}")
            try:
                self.client.detach_instances(
                    InstanceIds=[instance_id],
                    AutoScalingGroupName=asg_name,
                    ShouldDecrementDesiredCapacity=False,
                )
                logger.info(f"Detached {instance_id} from {asg_name}")
            except botocore.exceptions.ClientError:
                logger.exception(f"Failed to detach {instance_id} from {asg_name}")
