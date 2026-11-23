# WebWindow Android

Android wrapper for the original WebWindow proxy browser, extended with a **Direct mode** for opening websites in an Android native WebView (outside the HTML iframe), plus the original **Proxy mode**.

## Modes
- **Direct**: opens the selected website in a native Android WebView overlay with an address bar, back, go, and close controls. This avoids iframe restrictions and is generally more compatible with modern sites.
- **Proxy**: retains the original WebWindow UI and Flask proxy workflow. Some websites can still be blocked or partially rendered by proxying.

Direct mode is still Android WebView, not Chrome. Websites using unsupported browser features, DRM, bot protection, WebSockets, or other restrictions may not work. File downloads currently show a notification and are not yet saved by an in-app download manager.

## Build from a phone
1. Upload the contents of this folder to a GitHub repository (repository root).
2. Open **Actions** → **Build WebWindow APK** → **Run workflow**.
3. Download the `WebWindow-debug-apk` artifact from a successful workflow.
4. Extract and install `app-debug.apk`.

Termux is only optionally used to prepare/upload source; it is not required at runtime. Python/Flask runs inside the APK through Chaquopy for the Proxy mode and home UI.
