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

import inspect
import importlib
import pkgutil
from typing import Dict, Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validator
import boto3

import quarantine.plugins
from quarantine.plugins.abstract_plugin import AbstractPlugin
from quarantine.resources import SNS
from quarantine.schemas import INPUT

logger = Logger()


def iter_namespace(ns_pkg):
    # https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-namespace-packages
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


discovered_plugins = {
    name: importlib.import_module(name)
    for _, name, ispkg in iter_namespace(quarantine.plugins)
    if not ispkg
}

logger.debug(f"Discovered plugins: {discovered_plugins}")


@validator(inbound_schema=INPUT)
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> None:

    finding_id = event.get("id")
    instance_id = event.get("resource", {}).get("instanceDetails", {}).get("instanceId")
    if not instance_id:
        raise Exception("instanceId not found in request")

    logger.append_keys(instance_id=instance_id)

    session = boto3._get_default_session()

    plugins = []
    for _, plugin_module in discovered_plugins.items():
        clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
        for (_, c) in clsmembers:
            if issubclass(c, AbstractPlugin) and (c is not AbstractPlugin):
                plugins.append(c(session, instance_id, finding_id))

    logger.info(f"Loaded plugins: {plugins}")

    sns = SNS(session)

    for plugin in plugins:
        message = plugin.execute()
        if message is not None:
            sns.publish(instance_id, message)

    message = f"Instance {instance_id} successfully quarantined"
    sns.publish(instance_id, message)
