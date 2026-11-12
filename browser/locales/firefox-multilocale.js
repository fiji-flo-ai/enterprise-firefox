/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

// Default preferences of a multi-locale package (see multilocale.json). The
// repack adds this file to the package, it is not part of any other build.

// An empty value makes the browser follow the locales of the operating system.
pref("intl.locale.requested", "");

// Let the user choose among the packaged locales in the settings.
pref("intl.multilingual.enabled", true);
pref("intl.multilingual.liveReload", true);
