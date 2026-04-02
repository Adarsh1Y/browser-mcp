import threading
import time
import json
import base64
from io import BytesIO

try:
    import gi
    gi.require_version('WebKit', '4.1')
    from gi.repository import WebKit, GLib, Gdk, Gtk
    WEBKIT_AVAILABLE = True
except (ImportError, ValueError):
    WEBKIT_AVAILABLE = False


class WebKitBrowser:
    def __init__(self):
        if not WEBKIT_AVAILABLE:
            raise ImportError("WebKitGTK not available")
        
        self._lock = threading.Lock()
        self._result = None
        self._ready = threading.Event()
        
        Gtk.init([])
        
        self.view = WebKit.WebView()
        self.view.connect("load-changed", self._on_load_changed)
        
        settings = WebKit.Settings()
        settings.set_property("enable-javascript", True)
        settings.set_property("enable-html5-local-storage", True)
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
                "url": self.view.get_uri(),
                "title": self.view.get_title() or ""
            }

    def get_html(self) -> str:
        with self._lock:
            return self.view.get_main_frame().get_data_content().decode('utf-8', errors='ignore')

    def get_text(self) -> str:
        js = """
        document.body.innerText || document.documentElement.innerText || ''
        """
        return self.execute_js(js).strip()

    def click(self, selector: str, is_xpath: bool = False):
        if is_xpath:
            script = f"""
            (function() {{
                var el = document.evaluate('{selector}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (el) el.click();
                return el ? 'clicked' : 'not found';
            }})()
            """
        else:
            script = f"""
            (function() {{
                var el = document.querySelector('{selector}');
                if (el) el.click();
                return el ? 'clicked' : 'not found';
            }})()
            """
        return self.execute_js(script)

    def fill(self, selector: str, value: str):
        script = f"""
        (function() {{
            var el = document.querySelector('{selector}');
            if (el) {{
                el.value = '{value.replace("'", "\\'")}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return 'filled';
            }}
            return 'not found';
        }})()
        """
        return self.execute_js(script)

    def screenshot(self, path: str, full_page: bool = False) -> str:
        with self._lock:
            allocation = self.view.get_allocation()
            width, height = allocation.width, allocation.height
            
            surface = Gdk.cairo_surface_create_from_widget(self.view, -1, -1, width, height)
            
            from cairo import ImageSurface, FORMAT_ARGB32
            if full_page:
                content_height = self.view.get_main_frame().get_data_content().decode('utf-8', errors='ignore')
                full_surface = ImageSurface(FORMAT_ARGB32, width, height)
                cr = Context(full_surface)
                cr.set_source_surface(surface, 0, 0)
                cr.paint()
                full_surface.write_to_png(path)
            else:
                surface.write_to_png(path)
            
            return path

    def execute_js(self, script: str):
        with self._lock:
            result = self.view.evaluate_javascript(script, -1)
            if result:
                if isinstance(result, str):
                    return result
                try:
                    return json.loads(result.get_json())
                except:
                    return str(result)
            return None

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
                return results;
            }})()
            """
        else:
            script = f"""
            (function() {{
                var els = document.querySelectorAll('{selector}');
                return Array.from(els).map(function(el) {{
                    return el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ')[0] : '');
                }});
            }})()
            """
        result = self.execute_js(script)
        if isinstance(result, list):
            return result
        return []

    def get_cookies(self) -> list:
        with self._lock:
            cookie_manager = WebKit.WebContext.get_default().get_cookie_manager()
            return []


class Context:
    def __init__(self, surface):
        self._ctx = None
        
    def set_source_surface(self, surface, x, y):
        pass
    
    def paint(self):
        pass


def main():
    print("Starting Browser MCP Server...")
    print("WebKitGTK-based lightweight browser for MCP")
    print("\nInstall dependencies:")
    print("  apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1")
    print("\nRun with: python -m browser_mcp")


if __name__ == "__main__":
    main()
