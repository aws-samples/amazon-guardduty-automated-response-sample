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

import time
import os
from typing import Dict, Any, List, Optional

from aws_lambda_powertools import Logger
import boto3
import botocore

from quarantine.constants import BOTO3_CONFIG

EC2_INSTANCE_PROFILE_ARN = os.environ["EC2_INSTANCE_PROFILE_ARN"]

logger = Logger(child=True)

__all__ = ["EC2"]


class EC2:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("ec2", config=BOTO3_CONFIG)

    def get_console_screenshot(self, instance_id: str) -> str:
        """
        Get console screenshot
        """

        logger.info(f"Getting EC2 console screenshot from {instance_id}")
        try:
            response = self.client.get_console_screenshot(InstanceId=instance_id, WakeUp=True)
            logger.debug(f"Got EC2 console screenshot from {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to get EC2 console screenshot from {instance_id}")
            raise

        return response["ImageData"]

    def describe_instances(self, instance_id: str) -> Dict[str, Any]:
        """
        Describe instances
        """

        logger.info(f"Describing instance {instance_id}")
        try:
            response = self.client.describe_instances(InstanceIds=[instance_id])
            logger.debug(f"Described instance {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to describe instance {instance_id}")
            raise

        return response["Reservations"][0]["Instances"][0]

    def describe_security_groups(self, instance_id: str, vpc_id: str) -> Dict[str, Any]:
        """
        Describe security groups
        """

        params = {
            "Filters": [
                {"Name": "tag:SOC-Status", "Values": ["quarantined"]},
                {"Name": "tag:SOC-InstanceId", "Values": [instance_id]},
                {"Name": "vpc-id", "Values": [vpc_id]},
            ]
        }

        logger.info(f"Describing security groups in VPC {vpc_id} for instance {instance_id}")
        try:
            response = self.client.describe_security_groups(**params)
            logger.debug(f"Described security groups in VPC {vpc_id} for instance {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(
                f"Failed to describe security groups in {vpc_id} for instance {instance_id}"
            )
            raise

        return response.get("SecurityGroups", [])

    def create_snapshot(self, instance_id: str, volume_id: str) -> None:
        """
        Create an EBS snapshot
        """

        description = f"Security Response automated copy of {volume_id} for instance {instance_id}"

        logger.info(f"Creating snapshot of volume {volume_id}")
        try:
            self.client.create_snapshot(VolumeId=volume_id, Description=description)
            logger.debug(f"Created snapshot of volume {volume_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to create snapshot of volume {volume_id}")

    def enable_termination_protection(self, instance_id: str) -> None:
        """
        Enable instance termination protection
        """

        logger.info(f"Enabling termination protection on {instance_id}")
        try:
            self.client.modify_instance_attribute(
                InstanceId=instance_id, DisableApiTermination={"Value": True}
            )
            self.client.modify_instance_attribute(
                InstanceId=instance_id, DisableApiStop={"Value": True}
            )
            logger.debug(f"Enabled termination protection on {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to enable termination protection on {instance_id}")
            raise

    def enable_volume_termination_protection(
        self, instance_id: str, block_device_names: Optional[List[str]] = None
    ) -> None:
        """
        Enable EBS volume termination protection
        """

        if not block_device_names:
            return

        block_device_mappings = [
            {"DeviceName": device_name, "Ebs": {"DeleteOnTermination": False}}
            for device_name in block_device_names
        ]

        logger.info(f"Enabling volume termination protection on {instance_id}")
        try:
            self.client.modify_instance_attribute(
                InstanceId=instance_id, BlockDeviceMappings=block_device_mappings
            )
            logger.debug(f"Enabled volume termination protection on {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to enable volume termination protection on {instance_id}")
            raise

    def shutdown_behavior_stop(self, instance_id: str) -> None:
        """
        Set instance shutdown behavior to stop
        """

        logger.info(f"Modifying instance shutdown behavior to 'stop' on {instance_id}")
        try:
            self.client.modify_instance_attribute(
                InstanceId=instance_id,
                InstanceInitiatedShutdownBehavior={"Value": "stop"},
            )
            logger.debug(f"Modified instance shutdown behavior to 'stop' on {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(
                f"Failed to modify instance shutdown behavior to 'stop' on {instance_id}"
            )
            raise

    def remove_ec2_instance_profile(self, instance_id: str) -> None:
        """
        Remove any EC2 instance profile attached to an instance
        """

        params = {
            "Filters": [
                {"Name": "instance-id", "Values": [instance_id]},
                {"Name": "state", "Values": ["associating", "associated"]},
            ]
        }

        logger.debug("Describing IAM instance profile associations on {instance_id}")
        try:
            response = self.client.describe_iam_instance_profile_associations(**params)
            logger.debug(f"Described IAM instance profile associations on {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(
                f"Failed to describe IAM instance profile associations on {instance_id}"
            )
            raise

        associations = response.get("IamInstanceProfileAssociations", [])
        if not associations:
            logger.debug(f"No IAM instance profiles attached to {instance_id}")
            return

        for association in associations:
            profile_arn = association["IamInstanceProfile"]["Arn"]
            logger.info(f"Disassociating IAM instance profile {profile_arn} from {instance_id}")
            try:
                self.client.disassociate_iam_instance_profile(
                    AssociationId=association["AssociationId"]
                )
                logger.debug(f"Disassociated IAM instance profile {profile_arn} from {instance_id}")
            except botocore.exceptions.ClientError:
                logger.exception(
                    f"Failed to disassociate IAM instance profile {profile_arn} from {instance_id}"
                )

    def attach_ec2_instance_profile(self, instance_id: str, profile_arn: str) -> None:
        """
        Attach an IAM Instance Profile to an EC2 instance
        """
        logger.info(f"Associating IAM instance profile {profile_arn} to {instance_id}")
        try:
            self.client.associate_iam_instance_profile(
                IamInstanceProfile={"Arn": profile_arn},
                InstanceId=instance_id,
            )
            logger.debug(f"Associated IAM instance profile {profile_arn} to {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(
                f"Failed to associated IAM instance profile {profile_arn} to {instance_id}"
            )

    def create_security_group(self, instance_id: str, vpc_id: str, tags=None) -> str:
        """
        Create a security group with no access
        """

        now = int(time.time())

        params = {
            "GroupName": f"quarantine-{instance_id}-{now}",
            "Description": f"Quarantine group for {instance_id}",
            "VpcId": vpc_id,
        }

        if tags:
            params["TagSpecifications"] = [
                {
                    "ResourceType": "security-group",
                    "Tags": tags,
                }
            ]

        logger.info(f"Creating new isolation security group for {instance_id}")
        try:
            response = self.client.create_security_group(**params)
            logger.debug(f"Created isolation security group for {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to create isolation security group for {instance_id}")
            raise

        group_id = response["GroupId"]
        self.client.revoke_security_group_egress(
            GroupId=group_id,
            IpPermissions=[
                {
                    "IpProtocol": "-1",
                    "IpRanges": [
                        {"CidrIp": "0.0.0.0/0"},
                    ],
                },
            ],
        )
        return group_id

    def describe_network_interfaces(self, instance_id: str) -> List[Dict[str, Any]]:
        """
        Update the security groups for an instance
        """

        logger.info(f"Describing network interfaces on {instance_id}")
        try:
            response = self.client.describe_network_interfaces(
                Filters=[
                    {
                        "Name": "attachment.instance-id",
                        "Values": [instance_id],
                    },
                    {
                        "Name": "attachment.status",
                        "Values": ["attaching", "attached"],
                    },
                ]
            )
            logger.debug(f"Described network interfaces on {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to describe network interfaces on {instance_id}")

        return response.get("NetworkInterfaces", [])

    def update_security_groups(self, network_interface_id: str, group_id: str) -> None:
        """
        Update the security groups on a network interface
        """

        logger.info(f"Updating security groups on {network_interface_id} to {group_id}")
        try:
            self.client.modify_network_interface_attribute(
                NetworkInterfaceId=network_interface_id, Groups=[group_id]
            )
            logger.debug(f"Updated security groups on {network_interface_id} to {group_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to update security groups on {network_interface_id}")

    def create_tags(self, instance_id: str, tags=None) -> None:
        """
        Create new tags on an EC2 instance
        """

        if not tags:
            return

        params = {
            "Resources": [instance_id],
            "Tags": tags,
        }

        logger.info(f"Creating tags on {instance_id}")
        try:
            self.client.create_tags(**params)
            logger.debug(f"Created tags on {instance_id}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to create tags on {instance_id}")
