#!/usr/local/autopkg/python
#
# Copyright 2023 Andrew Zirkel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""See docstring for SMARTMirrorAppURLProvider class"""

from __future__ import absolute_import

import json
import re
from typing import List, Tuple

from autopkglib import URLGetter

__all__: List[str] = ["SMARTMirrorAppURLProvider"]

MY_URL: str=("https://montage-updates.displaynote.com/api/montage/rest/pub/releases/generic/f10632d2-9fbf-11e8-8999-ff918fb3468a/2.22.1.27915/update/info")


class SMARTMirrorAppURLProvider(URLGetter):
    """Provides URL to the latest SMARTMirrorApp release."""

    description = __doc__
    input_variables = {
        "url": {
            "required": False,
            "description": (
                f"(Advanced) URL for downloads.  Default is '{MY_URL}'."
            ),
            "default": MY_URL,
        },
    }
    output_variables = {
        "url": {"description": "URL to the latest SMARTMirrorApp product release."},
        "version": {
            "description": (
                "Version as specified in json"
            )
        },
        "filename": {
            "description": (
                "Package Fiile Name"
            )
        }
    }

    def main(self):
        """Provide a SMARTMirrorApp download URL"""
        url = self.env.get("url", MY_URL)
        headers = {
            "X-Release-Flavour": "smart",
            "X-Release-Channel": "released",
        }
        body = self.download(url,headers)
        json_data = json.loads(body)
        self.env["url"]=json_data["downloadUrl"]
        self.env["version"]=json_data["appVersionTag"]
        self.env["filename"]=json_data["fileName"]

        self.output(f"Found URL {self.env['url']}")


if __name__ == "__main__":
    PROCESSOR = SMARTMirrorAppURLProvider()
    PROCESSOR.execute_shell()