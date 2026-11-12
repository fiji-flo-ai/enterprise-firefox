# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

import mozunit

from mozpack.chrome.manifest import Manifest, ManifestContent, ManifestLocale
from mozpack.copier import FileRegistry
from mozpack.files import GeneratedFile, ManifestFile
from mozpack.packager import l10n
from test_packager import MockFinder


class TestL10NRepack(unittest.TestCase):
    def test_l10n_repack(self):
        foo = GeneratedFile(b"foo")
        foobar = GeneratedFile(b"foobar")
        qux = GeneratedFile(b"qux")
        bar = GeneratedFile(b"bar")
        baz = GeneratedFile(b"baz")
        dict_aa = GeneratedFile(b"dict_aa")
        dict_bb = GeneratedFile(b"dict_bb")
        dict_cc = GeneratedFile(b"dict_cc")
        barbaz = GeneratedFile(b"barbaz")
        lst = GeneratedFile(b"foo\nbar")
        app_finder = MockFinder({
            "bar/foo": foo,
            "chrome/foo/foobar": foobar,
            "chrome/qux/qux.properties": qux,
            "chrome/qux/baz/baz.properties": baz,
            "chrome/chrome.manifest": ManifestFile(
                "chrome",
                [
                    ManifestContent("chrome", "foo", "foo/"),
                    ManifestLocale("chrome", "qux", "en-US", "qux/"),
                ],
            ),
            "chrome.manifest": ManifestFile(
                "", [Manifest("", "chrome/chrome.manifest")]
            ),
            "dict/aa": dict_aa,
            "app/chrome/bar/barbaz.dtd": barbaz,
            "app/chrome/chrome.manifest": ManifestFile(
                "app/chrome", [ManifestLocale("app/chrome", "bar", "en-US", "bar/")]
            ),
            "app/chrome.manifest": ManifestFile(
                "app", [Manifest("app", "chrome/chrome.manifest")]
            ),
            "app/dict/bb": dict_bb,
            "app/dict/cc": dict_cc,
            "app/chrome/bar/search/foo.xml": foo,
            "app/chrome/bar/search/bar.xml": bar,
            "app/chrome/bar/search/lst.txt": lst,
            "META-INF/foo": foo,  # Stripped.
            "inner/META-INF/foo": foo,  # Not stripped.
            "app/META-INF/foo": foo,  # Stripped.
            "app/inner/META-INF/foo": foo,  # Not stripped.
        })
        app_finder.jarlogs = {}
        app_finder.base = "app"
        foo_l10n = GeneratedFile(b"foo_l10n")
        qux_l10n = GeneratedFile(b"qux_l10n")
        baz_l10n = GeneratedFile(b"baz_l10n")
        barbaz_l10n = GeneratedFile(b"barbaz_l10n")
        lst_l10n = GeneratedFile(b"foo\nqux")
        l10n_finder = MockFinder({
            "chrome/qux-l10n/qux.properties": qux_l10n,
            "chrome/qux-l10n/baz/baz.properties": baz_l10n,
            "chrome/chrome.manifest": ManifestFile(
                "chrome",
                [
                    ManifestLocale("chrome", "qux", "x-test", "qux-l10n/"),
                ],
            ),
            "chrome.manifest": ManifestFile(
                "", [Manifest("", "chrome/chrome.manifest")]
            ),
            "dict/bb": dict_bb,
            "dict/cc": dict_cc,
            "app/chrome/bar-l10n/barbaz.dtd": barbaz_l10n,
            "app/chrome/chrome.manifest": ManifestFile(
                "app/chrome",
                [ManifestLocale("app/chrome", "bar", "x-test", "bar-l10n/")],
            ),
            "app/chrome.manifest": ManifestFile(
                "app", [Manifest("app", "chrome/chrome.manifest")]
            ),
            "app/dict/aa": dict_aa,
            "app/chrome/bar-l10n/search/foo.xml": foo_l10n,
            "app/chrome/bar-l10n/search/qux.xml": qux_l10n,
            "app/chrome/bar-l10n/search/lst.txt": lst_l10n,
        })
        l10n_finder.base = "l10n"
        copier = FileRegistry()
        formatter = l10n.FlatFormatter(copier)

        l10n._repack(
            app_finder,
            l10n_finder,
            copier,
            formatter,
            ["dict", "chrome/**/search/*.xml"],
        )
        self.maxDiff = None

        repacked = {
            "bar/foo": foo,
            "chrome/foo/foobar": foobar,
            "chrome/qux-l10n/qux.properties": qux_l10n,
            "chrome/qux-l10n/baz/baz.properties": baz_l10n,
            "chrome/chrome.manifest": ManifestFile(
                "chrome",
                [
                    ManifestContent("chrome", "foo", "foo/"),
                    ManifestLocale("chrome", "qux", "x-test", "qux-l10n/"),
                ],
            ),
            "chrome.manifest": ManifestFile(
                "", [Manifest("", "chrome/chrome.manifest")]
            ),
            "dict/bb": dict_bb,
            "dict/cc": dict_cc,
            "app/chrome/bar-l10n/barbaz.dtd": barbaz_l10n,
            "app/chrome/chrome.manifest": ManifestFile(
                "app/chrome",
                [ManifestLocale("app/chrome", "bar", "x-test", "bar-l10n/")],
            ),
            "app/chrome.manifest": ManifestFile(
                "app", [Manifest("app", "chrome/chrome.manifest")]
            ),
            "app/dict/aa": dict_aa,
            "app/chrome/bar-l10n/search/foo.xml": foo_l10n,
            "app/chrome/bar-l10n/search/qux.xml": qux_l10n,
            "app/chrome/bar-l10n/search/lst.txt": lst_l10n,
            "inner/META-INF/foo": foo,
            "app/inner/META-INF/foo": foo,
        }

        self.assertEqual(
            dict((p, f.open().read()) for p, f in copier),
            dict((p, f.open().read()) for p, f in repacked.items()),
        )

    def test_add_locales(self):
        foo = GeneratedFile(b"foo")
        qux = GeneratedFile(b"qux")
        barbaz = GeneratedFile(b"barbaz")
        ftl = GeneratedFile(b"ftl")
        app_finder = MockFinder({
            "bar/foo": foo,
            "chrome/qux/qux.properties": qux,
            "chrome/chrome.manifest": ManifestFile(
                "chrome", [ManifestLocale("chrome", "qux", "en-US", "qux/")]
            ),
            "chrome.manifest": ManifestFile(
                "", [Manifest("", "chrome/chrome.manifest")]
            ),
            "localization/en-US/foo.ftl": ftl,
            "res/multilocale.txt": GeneratedFile(b"en-US"),
            "app/chrome/bar/barbaz.dtd": barbaz,
            "app/chrome/chrome.manifest": ManifestFile(
                "app/chrome", [ManifestLocale("app/chrome", "bar", "en-US", "bar/")]
            ),
            "app/chrome.manifest": ManifestFile(
                "app", [Manifest("app", "chrome/chrome.manifest")]
            ),
        })
        app_finder.jarlogs = {}

        def l10n_finder(locale):
            def content(name):
                return GeneratedFile(f"{name}_{locale}".encode())

            return MockFinder({
                f"chrome/{locale}/qux.properties": content("qux"),
                "chrome/chrome.manifest": ManifestFile(
                    "chrome", [ManifestLocale("chrome", "qux", locale, f"{locale}/")]
                ),
                "chrome.manifest": ManifestFile(
                    "", [Manifest("", "chrome/chrome.manifest")]
                ),
                f"localization/{locale}/foo.ftl": content("ftl"),
                "res/multilocale.txt": GeneratedFile(f"{locale},en-US".encode()),
                "default.locale": GeneratedFile(locale.encode()),
                f"app/chrome/{locale}/barbaz.dtd": content("barbaz"),
                "app/chrome/chrome.manifest": ManifestFile(
                    "app/chrome",
                    [ManifestLocale("app/chrome", "bar", locale, f"{locale}/")],
                ),
                "app/chrome.manifest": ManifestFile(
                    "app", [Manifest("app", "chrome/chrome.manifest")]
                ),
            })

        copier = FileRegistry()
        formatter = l10n.FlatFormatter(copier)

        l10n._add_locales(
            app_finder,
            [l10n_finder("x-one"), l10n_finder("x-two")],
            copier,
            formatter,
            {
                "res/multilocale.txt": b"x-one,x-two,en-US",
                "app/default.locale": b"multi",
            },
        )
        self.maxDiff = None

        packaged = {
            "bar/foo": foo,
            "chrome/qux/qux.properties": qux,
            "chrome/x-one/qux.properties": GeneratedFile(b"qux_x-one"),
            "chrome/x-two/qux.properties": GeneratedFile(b"qux_x-two"),
            "chrome/chrome.manifest": ManifestFile(
                "chrome",
                [
                    ManifestLocale("chrome", "qux", "en-US", "qux/"),
                    ManifestLocale("chrome", "qux", "x-one", "x-one/"),
                    ManifestLocale("chrome", "qux", "x-two", "x-two/"),
                ],
            ),
            "chrome.manifest": ManifestFile(
                "", [Manifest("", "chrome/chrome.manifest")]
            ),
            "localization/en-US/foo.ftl": ftl,
            "localization/x-one/foo.ftl": GeneratedFile(b"ftl_x-one"),
            "localization/x-two/foo.ftl": GeneratedFile(b"ftl_x-two"),
            "res/multilocale.txt": GeneratedFile(b"x-one,x-two,en-US"),
            "app/chrome/bar/barbaz.dtd": barbaz,
            "app/chrome/x-one/barbaz.dtd": GeneratedFile(b"barbaz_x-one"),
            "app/chrome/x-two/barbaz.dtd": GeneratedFile(b"barbaz_x-two"),
            "app/chrome/chrome.manifest": ManifestFile(
                "app/chrome",
                [
                    ManifestLocale("app/chrome", "bar", "en-US", "bar/"),
                    ManifestLocale("app/chrome", "bar", "x-one", "x-one/"),
                    ManifestLocale("app/chrome", "bar", "x-two", "x-two/"),
                ],
            ),
            "app/chrome.manifest": ManifestFile(
                "app", [Manifest("app", "chrome/chrome.manifest")]
            ),
            "app/default.locale": GeneratedFile(b"multi"),
        }

        self.assertEqual(
            dict((p, f.open().read()) for p, f in copier),
            dict((p, f.open().read()) for p, f in packaged.items()),
        )


if __name__ == "__main__":
    mozunit.main()
