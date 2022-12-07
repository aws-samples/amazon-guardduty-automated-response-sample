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

__all__ = ["ELB"]


class ELB:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("elb", config=BOTO3_CONFIG)

    def deregister_instance(self, instance_id: str) -> None:
        """
        Deregister instance from any classic ELBs
        """

        logger.info(f"Checking if instance {instance_id} is registered with any classic ELBs")
        try:
            response = self.client.describe_load_balancers()
            logger.debug("Described load balancers")
        except botocore.exceptions.ClientError:
            logger.exception("Failed to describe load balancers")
            raise

        for lb in response.get("LoadBalancerDescriptions", []):
            load_balancer_name = lb["LoadBalancerName"]
            found_instance = False

            instances = self.client.describe_instance_health(LoadBalancerName=load_balancer_name)
            for instance in instances.get("InstanceStates", []):
                if instance_id == instance["InstanceId"]:
                    logger.info(f"Found {instance_id} registered to ELB {load_balancer_name}")
                    found_instance = True
                    break

            if found_instance:
                params = {
                    "LoadBalancerName": load_balancer_name,
                    "Instances": [
                        {
                            "InstanceId": instance_id
                        }
                    ]
                }
                try:
                    self.client.deregister_instances_from_load_balancer(**params)
                    logger.info(f"Deregistered instance {instance_id} from ELB {load_balancer_name}")
                except botocore.exceptions.ClientError:
                    logger.exception(f"Failed to deregister instance {instance_id} from ELB {load_balancer_name}")
