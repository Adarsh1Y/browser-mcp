import threading
import time
import json
import os
import subprocess
import tempfile

try:
    import gi
    gi.require_version('WebKit2', '4.1')
    from gi.repository import WebKit2 as WebKit, GLib
    WEBKIT_AVAILABLE = True
except (ImportError, ValueError) as e:
    WEBKIT_AVAILABLE = False


class WebKitBrowser:
    def __init__(self, width: int = 1024, height: int = 768):
        if not WEBKIT_AVAILABLE:
            raise ImportError("WebKitGTK not available")
        
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self._result_ready = threading.Event()
        self._js_result = None
        self._snapshot_ready = threading.Event()
        self._snapshot_surface = None
        self._current_url = None
        
        from gi.repository import Gtk
        self._window = Gtk.Window()
        self._window.set_default_size(width, height)
        
        self.view = WebKit.WebView()
        self.view.connect("load-changed", self._on_load_changed)
        self.view.connect("notify::estimated-load-progress", self._on_progress_changed)
        
        context = self.view.get_context()
        if context:
            try:
                context.set_tls_errors_policy(WebKit.TLSErrorsPolicy.IGNORE)
            except Exception:
                pass
        
        settings = WebKit.Settings()
        settings.set_property("enable-javascript", True)
        settings.set_property("enable-webgl", False)
        self.view.set_settings(settings)
        
        self._window.add(self.view)
        self._window.show_all()
        
        self._window.set_keep_above(True)
        
        self._process_events(0.5)
        
        self._ready.clear()

    def show(self):
        """Show and raise the browser window."""
        self._window.present()
        self._window.show()
        self._process_events(0.1)

    def hide(self):
        """Hide the browser window."""
        self._window.hide()

    def set_size(self, width: int, height: int):
        """Set the window size."""
        self._window.resize(width, height)
        self._process_events(0.2)

    def _on_load_changed(self, view, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            self._ready.set()

    def _on_progress_changed(self, view, progress):
        if view.get_estimated_load_progress() >= 1.0:
            self._snapshot_ready.set()

    def _process_events(self, duration: float = 0.1):
        end_time = time.time() + duration
        while time.time() < end_time:
            GLib.MainContext.default().iteration(False)
            time.sleep(0.01)

    def navigate(self, url: str, wait: float = 2.0) -> dict:
        with self._lock:
            self._ready.clear()
            self._snapshot_ready.clear()
            self._current_url = url
            self.view.load_uri(url)
            
            for _ in range(300):
                if self._ready.is_set():
                    break
                self._process_events(0.1)
            
            time.sleep(wait)
            self._process_events(1.0)
            
            return {
                "url": self.view.get_uri() or url,
                "title": self.view.get_title() or ""
            }

    def get_html(self) -> str:
        with self._lock:
            self._process_events(0.5)
            script = "document.documentElement.outerHTML"
            return self._execute_js(script) or ""

    def get_text(self) -> str:
        with self._lock:
            self._process_events(0.5)
            script = "document.body ? document.body.innerText : document.documentElement.innerText"
            result = self._execute_js(script)
            return (result or "").strip()

    def _execute_js(self, script: str) -> str:
        self._js_result = None
        self._result_ready.clear()
        
        def callback(webview, result):
            try:
                js_result = webview.run_javascript_finish(result)
                if js_result:
                    self._js_result = js_result.get_js_value().to_string()
            except:
                self._js_result = None
            self._result_ready.set()
        
        self.view.run_javascript(script, None, callback)
        
        for _ in range(100):
            if self._result_ready.is_set():
                break
            self._process_events(0.1)
        
        return self._js_result

    def click(self, selector: str, is_xpath: bool = False):
        if is_xpath:
            script = f"(function() {{var el=document.evaluate('{selector}',document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue;if(el){{el.click();return'clicked';}}return'not found';}})()"
        else:
            script = f"(function() {{var el=document.querySelector('{selector}');if(el){{el.click();return'clicked';}}return'not found';}})()"
        return self._execute_js(script)

    def fill(self, selector: str, value: str):
        safe_value = value.replace("'", "\\'")
        script = f"(function(){{var el=document.querySelector('{selector}');if(el){{el.value='{safe_value}';el.dispatchEvent(new Event('input',{{bubbles:true}}));el.dispatchEvent(new Event('change',{{bubbles:true}}));return'filled';}}return'not found';}})()"
        return self._execute_js(script)

    def screenshot(self, path: str, full_page: bool = False) -> str:
        with self._lock:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
            
            self._process_events(1.0)
            
            native_result = self._screenshot_gtk(path, full_page)
            if native_result and os.path.exists(native_result) and os.path.getsize(native_result) > 1000:
                return native_result
            
            fallback_result = self._screenshot_wkhtmltopdf(path)
            if fallback_result:
                return fallback_result
            
            fallback_result = self._screenshot_webkit2png(path)
            if fallback_result:
                return fallback_result
            
            return path

    def _screenshot_gtk(self, path: str, full_page: bool) -> str:
        try:
            import cairo
            
            win = self.view.get_window()
            if not win:
                return ""
            
            allocation = self.view.get_allocation()
            width = allocation.width if allocation.width > 0 else 1024
            height = allocation.height if allocation.height > 0 else 768
            
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
            cr = cairo.Context(surface)
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            
            try:
                self.view.draw(cr)
            except Exception:
                pass
            
            surface.write_to_png(path)
            
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path
        except ImportError:
            pass
        except Exception as e:
            print(f"GTK screenshot error: {type(e).__name__}: {e}")
        return ""

    def _screenshot_wkhtmltopdf(self, path: str) -> str:
        try:
            if not self._current_url:
                return ""
            
            result = subprocess.run(
                ['wkhtmltopdf', '--width', '1024', '--height', '768', 
                 '--disable-javascript', self._current_url, path],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(path):
                if os.path.getsize(path) > 1000:
                    return path
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"wkhtmltopdf not available: {e}")
        except Exception as e:
            print(f"wkhtmltopdf error: {e}")
        return ""

    def _screenshot_webkit2png(self, path: str) -> str:
        try:
            result = subprocess.run(
                ['webkit2png', '-o', path, '-x', '1024', '768', self._current_url or ''],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if os.path.exists(path):
                    return path
                test_path = path.replace('.png', '-full.png')
                if os.path.exists(test_path):
                    os.rename(test_path, path)
                    return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            print(f"webkit2png error: {e}")
        return ""

    def find_elements(self, selector: str, is_xpath: bool = False):
        if is_xpath:
            script = f"(function(){{var nodes=document.evaluate('{selector}',document,null,XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null);var r=[];for(var i=0;i<nodes.snapshotLength;i++){{var el=nodes.snapshotItem(i);r.push(el.tagName+(el.id?'#'+el.id:'')+(el.className?'.'+el.className.split(' ')[0]:''));}}return JSON.stringify(r);}})()"
        else:
            script = f"(function(){{var els=document.querySelectorAll('{selector}');return JSON.stringify(Array.from(els).map(function(el){{return el.tagName+(el.id?'#'+el.id:'')+(el.className?'.'+el.className.split(' ')[0]:'');}}));}})()"
        
        result = self._execute_js(script)
        if result:
            try:
                return json.loads(result)
            except:
                return []
        return []

    def get_cookies(self) -> list:
        return []


def main():
    print("Starting Browser MCP Server...")
    print("WebKitGTK-based lightweight browser for MCP")
    print("\nInstall dependencies:")
    print("  Arch: sudo pacman -S webkit2gtk4.1 python-gobject python-cairo gobject-introspection")
    print("  Ubuntu/Debian: sudo apt install libwebkit2gtk-4.1-dev python3-gi python3-gi-cairo gir1.2-webkit2-4.1")
    print("\nOptional for screenshots:")
    print("  Arch: sudo pacman -S wkhtmltopdf")
    print("  Ubuntu: sudo apt install wkhtmltopdf")
    print("  Or: pip install webkit2png")
    print("\nRun with: python -m browser_mcp")


if __name__ == "__main__":
    main()
