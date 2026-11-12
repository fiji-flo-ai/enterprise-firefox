# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest
from mozunit import main

from gecko_taskgraph import GECKO
from gecko_taskgraph.transforms.l10n import parse_locales_file, parse_multilocale_file

CHANGESETS = {"de": "abc", "fr": "abc", "it": "def"}


def write_multilocales(tmp_path, multilocales):
    path = tmp_path / "multilocale.json"
    path.write_text(json.dumps(multilocales))
    return str(path)


def test_no_multilocale_file():
    assert parse_multilocale_file(None, CHANGESETS) == {}


def test_multilocale_takes_the_revision_of_its_locales(tmp_path):
    path = write_multilocales(tmp_path, {"multi": {"locales": ["en-US", "de", "fr"]}})
    assert parse_multilocale_file(path, CHANGESETS) == {"multi": "abc"}


def test_multilocale_with_a_locale_which_is_not_repacked(tmp_path):
    path = write_multilocales(tmp_path, {"multi": {"locales": ["de", "ja"]}})
    with pytest.raises(Exception, match="not repacked for this platform: ja"):
        parse_multilocale_file(path, CHANGESETS)


def test_multilocale_with_several_revisions(tmp_path):
    path = write_multilocales(tmp_path, {"multi": {"locales": ["de", "it"]}})
    with pytest.raises(Exception, match="must share one revision"):
        parse_multilocale_file(path, CHANGESETS)


@pytest.mark.parametrize(
    "platform", ("linux64", "linux64-aarch64", "macosx64", "win64", "win64-aarch64")
)
def test_in_tree_multilocales_are_repacked_for_enterprise(platform):
    changesets = parse_locales_file(
        f"{GECKO}/browser/locales/enterprise-l10n-changesets.json", platform=platform
    )
    multilocales = parse_multilocale_file(
        f"{GECKO}/browser/locales/multilocale.json", changesets
    )
    assert multilocales
    assert not set(multilocales) & set(changesets)


if __name__ == "__main__":
    main()
