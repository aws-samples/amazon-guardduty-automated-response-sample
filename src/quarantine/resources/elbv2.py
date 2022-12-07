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

from quarantine.constants import BOTO3_CONFIG

logger = Logger(child=True)

__all__ = ["ELBv2"]


class ELBv2:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("elbv2", config=BOTO3_CONFIG)

    def deregister_target(self, instance_id: str) -> None:
        """
        Deregister instance from any target groups
        """

        logger.info(f"Checking if instance {instance_id} is registered with any target groups")
        try:
            response = self.client.describe_target_groups()
            logger.debug("Described target groups")
        except botocore.exceptions.ClientError:
            logger.exception("Failed to describe target groups")
            raise

        for tg in response.get("TargetGroups", []):
            target_group_arn = tg["TargetGroupArn"]
            found_instance = False

            instances = self.client.describe_target_health(TargetGroupArn=target_group_arn)
            for target in instances.get("TargetHealthDescriptions", []):
                if instance_id == target["Target"]["Id"]:
                    logger.info(f"Found {instance_id} registered to target group {target_group_arn}")
                    found_instance = True
                    break

            if found_instance:
                params = {
                    "TargetGroupArn": target_group_arn,
                    "Targets": [
                        {
                            "Id": instance_id
                        }
                    ]
                }
                try:
                    self.client.deregister_targets(**params)
                    logger.info(f"Deregistered instance {instance_id} from target group {target_group_arn}")
                except botocore.exceptions.ClientError:
                    logger.exception(f"Failed to deregister instance {instance_id} from target group {target_group_arn}")
