#!/usr/bin/python

import urllib.parse
import urllib.request
import http.cookiejar
import ssl
import re

from html import unescape
from autopkglib import Processor, ProcessorError

__all__ = ["SibeliusURLProvider"]

BASE_URL=("https://my.avid.com")
LOGIN_URL=("https://my.avid.com/account/orientation/Login")
DOWNLOAD_URL = ("https://my.avid.com/products/")
REGEX = "https://cdn.avid.com/Sibelius/Sibelius.*ac\.dmg"
VERSION_REGEX = "\d{4}\.\d"
USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"

class SibeliusURLProvider(Processor):
    description = "Provides URL to the latest Sibelius release."
    input_variables = {
        "username": {
            "required": True,
            "description": ("Username for My Avid.")
        },
        "password": {
            "required": True,
            "description": ("Password for My Avid.")
        }
    }
    output_variables = {
        "url": {
            "description": "URL to the latest Sibelius release.",
        },
        "version": {
            "description": "Version in the form of: download.build (i.e. 1.64.6).",
        }
    }

    __doc__ = description

    def get_version(self, url):
        return re.search(VERSION_REGEX,url)[0].rstrip()

    def get_url(self, username, password):

        #Skip ssl verification
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # initiate the cookie jar (using : http.cookiejar and urllib.request)
        cookie_jar = http.cookiejar.CookieJar()
        #no ssl check
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar),
                                             urllib.request.HTTPSHandler(context=ctx))
        urllib.request.install_opener(opener)

        # first a simple request, just to get login page and parse out the token
        #       (using : urllib.request)
        FORM={'Theme' : '',
              'Email' : username,
              'Password' : password,
              'RememberMe' : 'false',
              'SyncAccounts' : 'false',
              'ReturnUrl' : DOWNLOAD_URL
              }
        # big thing! you need a referer for most pages! and correct headers are the key
        headers={"Content-Type":"application/x-www-form-urlencoded",
        "User-Agent":USER_AGENT,    # Chrome 80+ as per web search
        "Host":"my.avid.com",
        "Origin":"https://my.avid.com",
        "Referer":"https://my.avid.com/account/orientation?returnUrl=https%3a%2f%2fmy.avid.com%2fproducts%2f",
        "Accept":"application/json",
        }

        # now we prepare all we need for login
        #   data - with our payload (user/pass/token) urlencoded and encoded as bytes
        data = urllib.parse.urlencode(FORM)
        binary_data = data.encode('UTF-8')
        # and put the URL + encoded data + correct headers into our POST request
        #   btw, despite what I thought it is automatically treated as POST
        #   I guess because of byte encoded data field you don't need to say it like this:
        #       urllib.request.Request(authentication_url, binary_data, headers, method='POST')
        request = urllib.request.Request(LOGIN_URL, binary_data, headers)
        response = urllib.request.urlopen(request)
        contents = response.read()

        headers={
            "User-Agent":USER_AGENT,    # Chrome 80+ as per web search
            "Host":"my.avid.com",
            "X-Requested-With":"XMLHttpRequest",
            "Referer":DOWNLOAD_URL,
            "Accept":"*/*",
            "sec-ch-ua-platform":"macOS",
            "Sec-Fetch-Site":"same-origin",
            "Sec-Fetch-Mode":"cors",
            "Sec-Fetch-Mode":"empty",
            "sec-ch-ua":"\"Google Chrome\";v=\"95\", \"Chromium\";v=\"95\", \";Not A Brand\";v=\"99\""
            }
        request = urllib.request.Request(DOWNLOAD_URL,None,headers)
        response = urllib.request.urlopen(request)
        contents = response.read()

        # parse the page
        html = contents.decode("utf-8")
        #now we have "https://my.avid.com/products/"
        #get prod id
        PN_REGEX = "sibelius-buy-now\" name=\"(.+?)\""
        PN = re.search(PN_REGEX, html).group(1)
        #get api download url
        API_DOWNLOAD_REGEX = "/products/Api/ProductDownloads/" + PN + "\?.*showAddValue=False"
        API_DOWNLOAD_URL = re.search(API_DOWNLOAD_REGEX, html).group(0)
        API_DOWNLOAD_URL = BASE_URL + unescape(API_DOWNLOAD_URL)
        #get download url
        request = urllib.request.Request(API_DOWNLOAD_URL,None,headers)
        response = urllib.request.urlopen(request)
        contents = response.read()
        # parse the page
        html = contents.decode("utf-8")

        match = re.search(REGEX, html)
        pkg_url = match[0]

        return pkg_url

    def main(self):
        # Determine username and password.
        username = self.env.get("username")
        password = self.env.get("password")

        self.env["url"] = self.get_url(username, password)
        self.env["version"] = self.get_version(self.env["url"])
        self.output("Found URL %s" % self.env["url"])
        self.output("Found VERSION %s" % self.env["version"])


if __name__ == "__main__":
    processor = SibeliusURLProvider()
    processor.execute_shell()
