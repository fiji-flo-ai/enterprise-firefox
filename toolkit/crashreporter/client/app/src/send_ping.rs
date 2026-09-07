/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

//! An entry point for sending a crash ping.
//!
//! The program argument is the user application data directory (UAppData),
//! which holds the crash data directory and, on enterprise builds, felt.json.

use crate::std::{env, io::stdin};
use crate::{glean, logging, net::ping};

/// The crash data directory inside the user application data directory. Keep
/// in sync with `Config::get_data_dir`.
const CRASH_REPORTS_DIR: &str = "Crash Reports";

pub fn main() {
    logging::init();

    let mut args = env::args_os().skip(2);
    let app_data_dir = ::std::path::PathBuf::from(args.next().expect("no app data path provided"));
    let reason = args.next().expect("no crash reason provided");

    let extra: serde_json::Value =
        serde_json::from_reader(stdin()).expect("failed to read extra data from stdin");

    #[cfg_attr(any(mock, not(feature = "enterprise")), allow(unused_mut))]
    let mut options = glean::InitOptions {
        data_dir: app_data_dir.join(CRASH_REPORTS_DIR),
        locale: None,
        // Assume that this is only invoked to send a ping when upload is enabled.
        upload_enabled: true,
        #[cfg(feature = "enterprise")]
        server_url: None,
    };
    // No `ServerURL` annotation is available here, so the endpoint is derived
    // from the console address in AutoConfig (or, on generic builds, the
    // environment variable or felt.json).
    #[cfg(all(not(mock), feature = "enterprise"))]
    options.set_server_url(
        crate::enterprise_prefs::console_glean_url(None, Some(&app_data_dir))
            .expect("failed to resolve the enterprise telemetry endpoint"),
    );
    let _glean_handle = options.init().expect("failed to acquire Glean store");

    ping::CrashPing {
        extra: &extra,
        reason: reason.to_str(),
    }
    .send();

    // Increase our chances of sending the ping immediately by explicitly shutting down Glean.
    ::glean::shutdown();
}

/// Just initialize Glean to allow any unsubmitted pings to be sent.
pub fn cleanup_main() {
    logging::init();

    let mut args = env::args_os().skip(2);
    let app_data_dir = ::std::path::PathBuf::from(args.next().expect("no app data path provided"));
    let upload_enabled: bool = args
        .next()
        .expect("upload enabled missing")
        .to_str()
        .expect("non-unicode upload enabled value")
        .parse()
        .expect("invalid upload enabled value");

    #[cfg_attr(any(mock, not(feature = "enterprise")), allow(unused_mut))]
    let mut options = glean::InitOptions {
        data_dir: app_data_dir.join(CRASH_REPORTS_DIR),
        locale: None,
        upload_enabled,
        #[cfg(feature = "enterprise")]
        server_url: None,
    };
    #[cfg(all(not(mock), feature = "enterprise"))]
    options.set_server_url(
        crate::enterprise_prefs::console_glean_url(None, Some(&app_data_dir))
            .expect("failed to resolve the enterprise telemetry endpoint"),
    );
    let _glean_handle = options.init().expect("failed to acquire Glean store");

    // Sleep for a short period for Glean to do its thing in the background (and so that
    // `glean::shutdown()` won't log a warning about waiting for init to complete).
    std::thread::sleep(std::time::Duration::from_secs(2));

    // Glean shutdown will block (for a period) on at least one ping to be sent.
    ::glean::shutdown();
}
