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

logger = Logger(child=True)


class PreserveVolumes(AbstractPlugin):
    """
    Enable volume termination protection on all attached volumes
    """

    def execute(self) -> Optional[str]:
        try:
            instance_data = self.ec2.describe_instances(self.instance_id)

            block_device_mappings = instance_data.get("BlockDeviceMappings", [])
            if not block_device_mappings:
                logger.debug(f"No EBS volumes found on instance {self.instance_id}, skipping volume termination protection")
                return

            device_names = [block_device["DeviceName"] for block_device in block_device_mappings]
            if not device_names:
                logger.debug(f"No EBS device names found on instance {self.instance_id}, skipping volume termination protection")
                return

            logger.debug(f"Found EBS block devices: {device_names}")

            # Enable termination protection on volumes
            self.ec2.enable_volume_termination_protection(self.instance_id, device_names)

            message = f"Enabled volume termination protection on attached volumes {device_names} on instance {self.instance_id}"
        except Exception:
            message = f"Unable to enable volume termination protection on instance {self.instance_id}"
            logger.exception(message)

        return message
