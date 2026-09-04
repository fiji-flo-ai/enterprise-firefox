#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys

sys.path.append(os.path.dirname(__file__))

from felt_console_error import FeltConsoleErrorBase
from felt_tests import find_free_port


class FeltConsoleError(FeltConsoleErrorBase):
    # test_felt_error_insecure_certs navigates to an external host (badssl.com).
    # Keep the connectivity service from probing detectportal.firefox.com (its
    # real URLs are restored now), which is blocked on some CI and can mark the
    # browser offline, breaking that external load.
    EXTRA_PREFS = {"network.connectivity-service.enabled": False}

    def teardown(self):
        if not hasattr(self, "_child_driver"):
            self._manually_closed_child = True
        return super().teardown()

    def assert_xhrerror(
        self,
        login_location,
        expected_heading,
        selector=".felt-browser-error-no-network",
        error_msg=None,
        error_msg_contains=None,
    ):
        # Using wrong address as console address should trigger XHR error
        # handling
        with self._driver.using_prefs(
            {"enterprise.console.address": login_location}, default_branch=True
        ):
            self.login_location.value = ""
            self.submit_email()

            self.assert_error_bar_message(
                selector=selector,
                expected_heading=expected_heading,
                error_msg=error_msg,
                error_msg_contains=error_msg_contains,
                screenshot_name=f"{self._testMethodName}_xhrerror",
                source="xhr",
            )

    def assert_neterror(
        self,
        login_location,
        expected_heading,
        selector=".felt-browser-error-connection",
        error_msg=None,
        error_msg_contains=None,
    ):
        # Using correct address as console address and incorrect host during
        # login should trigger about:neterror error handling
        with self._driver.using_prefs(
            {"enterprise.console.address": f"http://localhost:{self.console_port}"},
            default_branch=True,
        ):
            self.login_location.value = login_location
            self.submit_email()

            self.assert_error_bar_message(
                selector=selector,
                expected_heading=expected_heading,
                error_msg=error_msg,
                error_msg_contains=error_msg_contains,
                screenshot_name=f"{self._testMethodName}_neterror",
                source="net",
            )

    def test_felt_unreachable_ip_shows_connection_error(self):
        # Port 1 is on Firefox's blocked-port list, producing a generic "network"
        # error key that resolves to "Unknown network error" via the felt-error-network

        # Trying to access :1 port will trigger a deniedPortAccess error. However
        # because it is happening during Redirect phase, the error pops from
        # nsHttpChannel directly and its handling bypasses about:neterror loading.
        #
        # Replicating the same behavior on Firefox show no page trying to load as well.
        # To replicate, instantiate a python http.server and serve a 302 redirection
        # to localhost:1.
        #
        # This allows to verify the handling of the SSO timeout logic.
        with self._driver.using_prefs(
            {
                "enterprise.console.address": f"http://localhost:{self.console_port}",
                "enterprise.sso.timeout_ms": 2000,
            },
            default_branch=True,
        ):
            self.login_location.value = "http://127.0.0.1:1"
            self.submit_email()

            self.assert_error_bar_message(
                selector=".felt-browser-error-sso-timeout",
                expected_heading="Sign-in timed out",
                screenshot_name=f"{self._testMethodName}_sso",
                source="reset",
            )

        self.assert_xhrerror(
            login_location="http://127.0.0.1:1",
            expected_heading="Unable to connect",
            selector=".felt-browser-error-connection",
            error_msg="Unknown network error",
        )

    def test_felt_nonexistent_domain_shows_no_network_error(self):
        self.assert_neterror(
            login_location="http://nonexistent.localdomain:80",
            expected_heading="Server not found",
            error_msg="Try connecting on a different device. Check your modem or router. Disconnect and reconnect to Wi-Fi.",
        )

        # dnsNotFound which renders the no-network bar rather than the connection error bar
        # XHR error handling was required to be different per UX request
        self.assert_xhrerror(
            login_location="http://nonexistent.localdomain:80",
            expected_heading="No network connection",
            error_msg="Please check your internet connection and try again.",
        )

    def test_felt_ssl_mismatch_shows_connection_error(self):
        self.assert_neterror(
            login_location=f"https://localhost:{self.console_port}",
            expected_heading="Secure Connection Failed",
        )

        self.assert_xhrerror(
            login_location=f"https://localhost:{self.console_port}",
            selector=".felt-browser-error-connection",
            expected_heading="Unable to connect",
        )

    def test_felt_error_details_include_console_address(self):
        # connectionFailure with host substitution so the console address appears in details.
        refused_port = find_free_port()

        self.assert_neterror(
            login_location=f"http://localhost:{refused_port}",
            expected_heading="Unable to connect",
            error_msg=f"{self.get_brand_name()} can’t connect to the server at localhost:{refused_port}",
        )

        self.assert_xhrerror(
            login_location=f"http://localhost:{refused_port}",
            selector=".felt-browser-error-connection",
            expected_heading="Unable to connect",
            error_msg=f"{self.get_brand_name()} can’t connect to the server at localhost:{refused_port}",
        )

    def test_felt_error_insecure_certs(self):
        self.assert_neterror(
            login_location="https://wrong.host.badssl.com/sso_url",
            expected_heading="Unable to connect",
            error_msg=f"{self.get_brand_name()} spotted a potentially serious security issue with wrong.host.badssl.com. Someone pretending to be the site could try to steal things like credit card info, passwords, or emails.",
        )

        self.assert_xhrerror(
            login_location="https://wrong.host.badssl.com/sso_url",
            selector=".felt-browser-error-connection",
            expected_heading="Unable to connect",
            error_msg=f"{self.get_brand_name()} spotted a potentially serious security issue with wrong.host.badssl.com. Someone pretending to be the site could try to steal things like credit card info, passwords, or emails.",
        )
