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

import base64
from typing import Optional

from aws_lambda_powertools import Logger

from quarantine.plugins.abstract_plugin import AbstractPlugin

logger = Logger(child=True)


class ConsoleScreenshot(AbstractPlugin):
    """
    Get a screenshot of the EC2 console and upload to S3
    """

    def execute(self) -> Optional[str]:
        try:
            image_data = self.ec2.get_console_screenshot(self.instance_id)
            key = f"console_screenshot_{self.instance_id}.jpg"
            screenshot = base64.b64decode(image_data)
            self.s3.put_object(self.instance_id, key, screenshot)
            message = f"Successfully captured console screen shot: {key}"
        except Exception:
            message = f"Unable to get screenshot from instance {self.instance_id}"
            logger.exception(message)

        return message
