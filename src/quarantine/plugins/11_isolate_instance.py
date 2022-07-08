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

from typing import Optional

from aws_lambda_powertools import Logger

from quarantine.plugins.abstract_plugin import AbstractPlugin
from quarantine.utils import now

logger = Logger(child=True)


class IsolateInstance(AbstractPlugin):
    """
    Isolate the EC2 instance by moving any attached network interfaces into new security groups
    """

    def execute(self) -> Optional[str]:
        try:
            network_interfaces = self.ec2.describe_network_interfaces(self.instance_id)
            if not network_interfaces:
                logger.info(f"No network interfaces found on instance {self.instance_id}")
                return

            vpc_ids = {network_interface["VpcId"] for network_interface in network_interfaces}
            logger.info(
                f"Found {len(network_interfaces)} network interface(s) in {len(vpc_ids)} VPCs"
            )

            tags = [
                {
                    "Key": "Name",
                    "Value": f"quarantine-{self.instance_id}",
                },
                {
                    "Key": "SOC-InstanceId",
                    "Value": self.instance_id,
                },
                {
                    "Key": "SOC-Status",
                    "Value": "quarantined",
                },
                {
                    "Key": "SOC-ContainedAt",
                    "Value": now(),
                },
                {
                    "Key": "SOC-FindingId",
                    "Value": self.finding_id,
                },
                {
                    "Key": "SOC-FindingSource",
                    "Value": "GuardDuty",
                },
            ]

            vpc_map = {}
            for vpc_id in vpc_ids:

                existing_sg = self.ec2.describe_security_groups(self.instance_id, vpc_id)
                if existing_sg:
                    vpc_map[vpc_id] = existing_sg[0]["GroupId"]
                else:
                    vpc_map[vpc_id] = self.ec2.create_security_group(self.instance_id, vpc_id, tags)

            for network_interface in network_interfaces:
                group_id = vpc_map.get(network_interface["VpcId"])
                if group_id:
                    self.ec2.update_security_groups(
                        network_interface["NetworkInterfaceId"], group_id
                    )

            message = f"Isolated instance {self.instance_id} into restricted security groups"
        except Exception:
            message = f"Unable to isolate instance {self.instance_id}"
            logger.exception(message)

        return message
