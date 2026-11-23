# WebWindow Android build notes

This source keeps the original WebWindow `app.py` and `templates/index.html` and adds an Android native WebView Direct mode.


## Modes
- **Direct**: native Android WebView overlay with URL bar and Back/Go/Close. Sites load directly, not inside a proxy iframe.
- **Proxy**: original Flask proxy-based website frames are retained.

Direct mode improves compatibility with iframe-blocking sites but is not a guarantee for every website. WebView is not Chrome and DRM, bot protection, unsupported APIs, WebSockets, or site restrictions may still cause issues. Download handling is not yet a full download manager.

## Build APK from a phone
1. Upload the contents of this project to a GitHub repository root.
2. In GitHub, open **Actions** → **Build WebWindow APK**.
3. Select **Run workflow** and wait for a successful run.
4. Download the **WebWindow-debug-apk** artifact and extract `app-debug.apk`.
5. Install the APK on your Android phone.

The installed app runs Python/Flask internally via Chaquopy for its home screen and Proxy mode. Termux is not required at runtime.
