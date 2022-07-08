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


class TagInstance(AbstractPlugin):
    """
    Tag the instance
    """

    def execute(self) -> Optional[str]:
        tags = [
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

        try:
            self.ec2.create_tags(self.instance_id, tags)
            message = f"Added incident tags to instance {self.instance_id}"
        except Exception:
            message = f"Unable to add tags to instance {self.instance_id}"
            logger.exception(message)

        return message
