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

from abc import ABC, abstractmethod
from typing import Optional

import boto3

from quarantine.resources import AutoScaling, EC2, ELB, ELBv2, S3, SSM


class AbstractPlugin(ABC):
    def __init__(self, session: boto3.Session, instance_id: str, finding_id: str) -> None:
        self.s3 = S3(session)
        self.ec2 = EC2(session)
        self.autoscaling = AutoScaling(session)
        self.ssm = SSM(session)
        self.elb = ELB(session)
        self.elbv2 = ELBv2(session)

        self.instance_id = instance_id
        self.finding_id = finding_id

    @abstractmethod
    def execute(self) -> Optional[str]:
        """
        Plugins must implement this method.

        If a plugin returns a string, it will be published to the SNS topic.
        """
        raise NotImplementedError
