package com.webwindow.app

import android.app.Activity
import android.os.Bundle
import android.view.View
import android.view.Gravity
import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.DownloadListener
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.EditText
import android.widget.TextView
import android.widget.Button
import android.widget.Toast
import android.graphics.Color
import android.graphics.Typeface
import android.view.ViewGroup
import android.content.Context
import android.graphics.Bitmap
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : Activity() {
    private lateinit var root: FrameLayout
    private lateinit var homeWebView: WebView
    private var directWebView: WebView? = null
    private var directBar: LinearLayout? = null
    private var fullscreenView: View? = null
    private var fullscreenCallback: WebChromeClient.CustomViewCallback? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(16, 23, 34)
        window.navigationBarColor = Color.rgb(16, 23, 34)

        try {
            if (!Python.isStarted()) Python.start(AndroidPlatform(this))
            Python.getInstance().getModule("embedded_server").callAttr("start_server")
        } catch (e: Exception) {
            Toast.makeText(this, "Backend Python gagal dimulai: ${e.message}", Toast.LENGTH_LONG).show()
        }

        root = FrameLayout(this)
        homeWebView = WebView(this)
        configureWebView(homeWebView, false)
        homeWebView.addJavascriptInterface(DirectBridge(), "WebWindowAndroid")
        homeWebView.webViewClient = WebViewClient()
        homeWebView.webChromeClient = WebChromeClient()
        homeWebView.setBackgroundColor(Color.rgb(16, 23, 34))
        root.addView(homeWebView, FrameLayout.LayoutParams(-1, -1))
        setContentView(root)
        homeWebView.loadUrl("http://127.0.0.1:5000/")
    }

    private fun configureWebView(view: WebView, direct: Boolean) {
        view.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            loadsImagesAutomatically = true
            mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
            mediaPlaybackRequiresUserGesture = false
            javaScriptCanOpenWindowsAutomatically = true
            setSupportMultipleWindows(false)
            if (direct) userAgentString = userAgentString.replace("; wv", "")
        }
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(view, true)
        view.setBackgroundColor(Color.WHITE)
        view.webViewClient = object : WebViewClient() {
            override fun onPageStarted(v: WebView, url: String, favicon: Bitmap?) {
                directBar?.findViewById<EditText>(1001)?.setText(url)
            }
        }
        view.webChromeClient = object : WebChromeClient() {
            override fun onShowCustomView(view: View, callback: CustomViewCallback) {
                if (fullscreenView != null) { callback.onCustomViewHidden(); return }
                fullscreenView = view
                fullscreenCallback = callback
                root.addView(view, FrameLayout.LayoutParams(-1, -1))
                directBar?.visibility = View.GONE
            }
            override fun onHideCustomView() {
                fullscreenView?.let { root.removeView(it) }
                fullscreenView = null
                fullscreenCallback?.onCustomViewHidden()
                fullscreenCallback = null
                directBar?.visibility = View.VISIBLE
            }
        }
        if (direct) {
            view.setDownloadListener(DownloadListener { url, _, _, _, _ ->
                Toast.makeText(this, "Link download: gunakan browser atau pengelola unduhan untuk menyimpan file", Toast.LENGTH_LONG).show()
            })
        }
    }


    inner class DirectBridge {
        @android.webkit.JavascriptInterface
        fun openDirect(url: String) {
            runOnUiThread { showDirectBrowser(url) }
        }
        @android.webkit.JavascriptInterface
        fun closeDirect() {
            runOnUiThread { closeDirectBrowser() }
        }
    }

    private fun showDirectBrowser(url: String) {
        if (!url.startsWith("https://", true) && !url.startsWith("http://", true)) {
            Toast.makeText(this, "URL hanya HTTP atau HTTPS", Toast.LENGTH_SHORT).show()
            return
        }
        closeDirectBrowser()
        val bar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setBackgroundColor(Color.rgb(22, 31, 45))
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(6), dp(5), dp(6), dp(5))
        }
        fun button(label: String, action: () -> Unit): Button = Button(this).apply {
            text = label
            textSize = 12f
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.rgb(45, 61, 83))
            setPadding(dp(4), 0, dp(4), 0)
            setOnClickListener { action() }
        }
        val browser = WebView(this)
        directWebView = browser
        configureWebView(browser, true)
        val back = button("‹") { if (browser.canGoBack()) browser.goBack() else closeDirectBrowser() }
        val address = EditText(this).apply {
            id = 1001
            singleLine = true
            textSize = 13f
            setTextColor(Color.WHITE)
            setHintTextColor(Color.LTGRAY)
            hint = "Alamat website"
            setPadding(dp(8), 0, dp(8), 0)
            setBackgroundColor(Color.rgb(39, 51, 70))
            setText(url)
            imeOptions = android.view.inputmethod.EditorInfo.IME_ACTION_GO
            setOnEditorActionListener { _, actionId, _ ->
                if (actionId == android.view.inputmethod.EditorInfo.IME_ACTION_GO) {
                    loadAddress(browser, text.toString()); true
                } else false
            }
        }
        val go = button("Go") { loadAddress(browser, address.text.toString()) }
        val close = button("×") { closeDirectBrowser() }
        bar.addView(back, LinearLayout.LayoutParams(dp(40), dp(42)))
        bar.addView(address, LinearLayout.LayoutParams(0, dp(42), 1f))
        bar.addView(go, LinearLayout.LayoutParams(dp(45), dp(42)))
        bar.addView(close, LinearLayout.LayoutParams(dp(40), dp(42)))
        directBar = bar
        val browserLayer = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        browserLayer.addView(bar, LinearLayout.LayoutParams(-1, dp(52)))
        browserLayer.addView(browser, LinearLayout.LayoutParams(-1, 0, 1f))
        root.addView(browserLayer, FrameLayout.LayoutParams(-1, -1))
        browser.tag = browserLayer
        browser.loadUrl(url)
    }

    private fun loadAddress(webView: WebView, raw: String) {
        val value = raw.trim()
        if (value.isBlank()) return
        val url = if (value.startsWith("http://", true) || value.startsWith("https://", true)) value
                  else if (value.contains('.') && !value.contains(' ')) "https://$value"
                  else "https://www.google.com/search?q=" + android.net.Uri.encode(value)
        webView.loadUrl(url)
    }

    private fun closeDirectBrowser() {
        val browser = directWebView
        if (browser != null) {
            val layer = browser.tag as? View
            layer?.let { root.removeView(it) }
            browser.stopLoading()
            browser.destroy()
        }
        directWebView = null
        directBar = null
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    override fun onBackPressed() {
        if (fullscreenView != null) {
            directWebView?.webChromeClient?.onHideCustomView()
            return
        }
        val browser = directWebView
        if (browser != null) {
            if (browser.canGoBack()) browser.goBack() else closeDirectBrowser()
            return
        }
        if (homeWebView.canGoBack()) homeWebView.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        closeDirectBrowser()
        if (::homeWebView.isInitialized) homeWebView.destroy()
        super.onDestroy()
    }
}
