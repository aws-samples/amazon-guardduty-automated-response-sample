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

import os
from typing import Union

from aws_lambda_powertools import Logger
import boto3
import botocore

from quarantine.utils import get_prefix
from quarantine.constants import BOTO3_CONFIG

BUCKET_NAME = os.environ["ARTIFACT_BUCKET"]
AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]

logger = Logger(child=True)

__all__ = ["S3"]


class S3:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("s3", config=BOTO3_CONFIG)

    def put_object(self, instance_id: str, key: str, body: Union[bytes, str]) -> None:
        prefix = get_prefix(instance_id)

        params = {
            "ACL": "bucket-owner-full-control",
            "Bucket": BUCKET_NAME,
            "Key": f"{prefix}/{key}",
            "Metadata": {"instance_id": instance_id},
            "ExpectedBucketOwner": AWS_ACCOUNT_ID,
        }
        logger.debug(params)
        params["Body"] = body  # the body is separate so its not logged

        logger.debug(f"Uploading s3://{BUCKET_NAME}/{prefix}/{key}")
        try:
            self.client.put_object(**params)
            logger.debug(f"Uploaded s3://{BUCKET_NAME}/{prefix}/{key}")
        except botocore.exceptions.ClientError:
            logger.exception(f"Failed to upload s3://{BUCKET_NAME}/{prefix}/{key}")
