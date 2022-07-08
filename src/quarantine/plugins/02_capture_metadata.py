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
import tempfile

from aws_lambda_powertools import Logger

from quarantine.plugins.abstract_plugin import AbstractPlugin
from quarantine.utils import json_dumps

logger = Logger(child=True)


class CaptureMetadata(AbstractPlugin):
    """
    Collect EC2 instance metadata upload to S3
    """

    def execute(self) -> Optional[str]:
        key = f"metadata_file_{self.instance_id}.json"

        try:
            # Capture instance metadata
            instance_data = self.ec2.describe_instances(self.instance_id)
            with tempfile.TemporaryFile() as fp:
                fp.write(json_dumps(instance_data).encode("utf-8"))
                fp.seek(0)

                self.s3.put_object(self.instance_id, key, fp)

            logger.info(f"Captured instance metadata for instance {self.instance_id}")
            message = f"Successfully captured instance metadata: {key}"
        except Exception:
            message = f"Unable to capture instance metadata on instance {self.instance_id}"
            logger.exception(message)

        return message
