from rubicon.objc import objc_method

from toga_cocoa.libs import *

from .base import Widget

import asyncio


class TogaWebView(WebView):
    @objc_method
    def webView_didFinishLoadForFrame_(self, sender, frame) -> None:
        if self.interface.on_webview_load:
            self.interface.on_webview_load(self.interface)

    @objc_method
    def acceptsFirstResponder(self) -> bool:
        return True

    @objc_method
    def keyDown_(self, event) -> None:
        print('in keyDown', event.keyCode)
        if self.interface.on_key_down:
            self.interface.on_key_down(event.keyCode, event.modifierFlags)

    @objc_method
    def touchBar(self):
        # Disable the touchbar.
        return None


class WebKit1WebView(Widget):
    def create(self):
        self.native = TogaWebView.alloc().init()
        self.native.interface = self.interface

        self.native.downloadDelegate = self.native
        self.native.frameLoadDelegate = self.native
        self.native.policyDelegate = self.native
        self.native.resourceLoadDelegate = self.native
        self.native.uIDelegate = self.native

        # Add the layout constraints
        self.add_constraints()

    def get_dom(self):
        # Utilises Step 2) of:
        # https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/DisplayWebContent/Tasks/SaveAndLoad.html
        html = self.native.mainFrame.DOMDocument.documentElement.outerHTML  ##domDocument.markupString
        return html

    def set_url(self, value):
        if value:
            request = NSURLRequest.requestWithURL(NSURL.URLWithString(self.interface.url))
            self.native.mainFrame.loadRequest(request)

    def set_content(self, root_url, content):
        self.native.mainFrame.loadHTMLString_baseURL_(content, NSURL.URLWithString(root_url))

    def set_user_agent(self, value):
        self.native.customUserAgent = value if value else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8"

    def evaluate(self, javascript):
        """
        Evaluate a JavaScript expression

        :param javascript: The javascript expression
        :type  javascript: ``str``
        """
        return self.native.stringByEvaluatingJavaScriptFromString(javascript)


if WKWebView is not None:  # WKWebView is only available under macOS 10.10 or newer.
    class TogaWKWebView(WKWebView):
        @objc_method
        def webView_didFinish_(self, navi):
            if self.interface.on_webview_load:
            self.interface.on_webview_load(self.interface)

        @objc_method
        def acceptsFirstResponder(self) -> bool:
            return True

        @objc_method
        def keyDown_(self, event) -> None:
            print('in keyDown', event.keyCode)
            if self.interface.on_key_down:
                self.interface.on_key_down(event.keyCode, event.modifierFlags)

        @objc_method
        def touchBar(self):
            # Disable the touchbar.
            return None

    class WebKit2WebView(Widget):
        def create(self):
            self.native = TogaWKWebView.alloc().init()
            self.native.interface = self.interface

            self.native.uiDelegate = self.native
            self.native.navigationDelegate = self.native

            self.add_constraints()

        def get_dom(self):
            return self.evaluate(
                'document.getElementsByTagName("html")[0].outerHTML')

        def set_url(self, value):
            if value:
                self.interface.url = value

            request = NSURLRequest.requestWithURL(NSURL.URLWithString(
                self.interface.url))
            self.native.load(request)

        def set_content(self, root_url, content):
            self.native.loadHTMLString_baseURL_(
                content, NSURL.URLWithString(root_url))

        def set_user_agent(self, value):
            self.native.customUserAgent = value

        def evaluate(self, js_str):
            fur = asyncio.Future()

            def when_finish(result, err):
                if fur.done():
                    return

                if err:
                    # Is NSError a subclass of BaseException?
                    fur.set_exception(RuntimeError(err))

                else:
                    fur.set_result(result)

            self.native.evaluateJavaScript_completionHandler_(
                js_str, when_finish)

            return fur

    WebView = WebKit2WebView

else:
    WebView = WebKit1WebView
