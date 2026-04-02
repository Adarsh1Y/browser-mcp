import threading
import time
import json
import os

try:
    import gi
    gi.require_version('WebKit2', '4.1')
    from gi.repository import WebKit2 as WebKit, GLib, GdkPixbuf
    Gtk = None
    WEBKIT_AVAILABLE = True
except (ImportError, ValueError) as e:
    WEBKIT_AVAILABLE = False


class WebKitBrowser:
    def __init__(self):
        if not WEBKIT_AVAILABLE:
            raise ImportError("WebKitGTK not available")
        
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._js_result = None
        self._js_ready = threading.Event()
        
        if Gtk:
            Gtk.init([])
        
        self.view = WebKit.WebView()
        self.view.connect("load-changed", self._on_load_changed)
        
        settings = WebKit.Settings()
        settings.set_property("enable-javascript", True)
        settings.set_property("enable-webgl", False)
        settings.set_property("enable-accelerated-2d-canvas", False)
        self.view.set_settings(settings)
        
        self._ready.clear()

    def _on_load_changed(self, view, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            self._ready.set()

    def navigate(self, url: str, wait: float = 2.0) -> dict:
        with self._lock:
            self._ready.clear()
            self.view.load_uri(url)
            self._ready.wait(timeout=30)
            time.sleep(wait)
            
            return {
                "url": self.view.get_uri() or url,
                "title": self.view.get_title() or ""
            }

    def get_html(self) -> str:
        with self._lock:
            try:
                page = self.view.get_page()
                if page:
                    return page.get_html() or ""
            except:
                pass
            return ""

    def get_text(self) -> str:
        result = self.run_javascript_sync("document.body ? document.body.innerText : document.documentElement.innerText")
        return (result or "").strip()

    def click(self, selector: str, is_xpath: bool = False):
        if is_xpath:
            script = f"""
            (function() {{
                var el = document.evaluate('{selector}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (el) {{ el.click(); return 'clicked'; }}
                return 'not found';
            }})()
            """
        else:
            script = f"""
            (function() {{
                var el = document.querySelector('{selector}');
                if (el) {{ el.click(); return 'clicked'; }}
                return 'not found';
            }})()
            """
        return self.run_javascript_sync(script)

    def fill(self, selector: str, value: str):
        safe_value = value.replace("'", "\\'")
        script = f"""
        (function() {{
            var el = document.querySelector('{selector}');
            if (el) {{
                el.value = '{safe_value}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return 'filled';
            }}
            return 'not found';
        }})()
        """
        return self.run_javascript_sync(script)

    def screenshot(self, path: str, full_page: bool = False) -> str:
        with self._lock:
            try:
                surface = self.view.get_snapshot(WebKit.SnapshotRegion.VISIBLE, None)
                if surface:
                    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
                    surface.write_to_png(path)
                    return path
            except Exception as e:
                print(f"Screenshot error: {e}")
            return path

    def run_javascript_sync(self, script: str):
        with self._lock:
            loop = GLib.MainLoop()
            result_holder = [None]
            
            def callback(webview, result, loop):
                try:
                    js_result = webview.run_javascript_finish(result)
                    if js_result:
                        result_holder[0] = js_result.get_js_value().to_string()
                except Exception as e:
                    result_holder[0] = None
                finally:
                    loop.quit()
            
            self.view.run_javascript(script, None, callback, loop)
            loop.run()
            return result_holder[0]

    def find_elements(self, selector: str, is_xpath: bool = False):
        if is_xpath:
            script = f"""
            (function() {{
                var nodes = document.evaluate('{selector}', document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                var results = [];
                for (var i = 0; i < nodes.snapshotLength; i++) {{
                    var el = nodes.snapshotItem(i);
                    results.push(el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ')[0] : ''));
                }}
                return JSON.stringify(results);
            }})()
            """
        else:
            script = f"""
            (function() {{
                var els = document.querySelectorAll('{selector}');
                return JSON.stringify(Array.from(els).map(function(el) {{
                    return el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ')[0] : '');
                }}));
            }})()
            """
        result = self.run_javascript_sync(script)
        if result:
            try:
                return json.loads(result)
            except:
                return []
        return []

    def get_cookies(self) -> list:
        with self._lock:
            try:
                context = self.view.get_context()
                if context:
                    cookie_manager = context.get_cookie_manager()
                    return []
            except:
                pass
            return []


def main():
    print("Starting Browser MCP Server...")
    print("WebKitGTK-based lightweight browser for MCP")
    print("\nInstall dependencies:")
    print("  Arch: sudo pacman -S webkit2gtk4.1 python-gobject python-cairo gobject-introspection")
    print("  Ubuntu/Debian: sudo apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1")
    print("\nRun with: python -m browser_mcp")


if __name__ == "__main__":
    main()
