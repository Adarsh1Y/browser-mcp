import threading
import time
import json
import os

try:
    import gi
    gi.require_version('WebKit2', '4.1')
    from gi.repository import WebKit2 as WebKit, GLib
    WEBKIT_AVAILABLE = True
except (ImportError, ValueError) as e:
    WEBKIT_AVAILABLE = False


class WebKitBrowser:
    def __init__(self):
        if not WEBKIT_AVAILABLE:
            raise ImportError("WebKitGTK not available")
        
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self._result_ready = threading.Event()
        self._js_result = None
        
        self.view = WebKit.WebView()
        self.view.connect("load-changed", self._on_load_changed)
        
        context = self.view.get_context()
        if context:
            context.set_tls_errors_policy(WebKit.TLSErrorsPolicy.IGNORE)
        
        settings = WebKit.Settings()
        settings.set_property("enable-javascript", True)
        settings.set_property("enable-webgl", False)
        self.view.set_settings(settings)
        
        self._ready.clear()

    def _on_load_changed(self, view, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            self._ready.set()

    def _process_events(self, duration: float = 0.1):
        end_time = time.time() + duration
        while time.time() < end_time:
            GLib.MainContext.default().iteration(False)
            time.sleep(0.01)

    def navigate(self, url: str, wait: float = 2.0) -> dict:
        with self._lock:
            self._ready.clear()
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
            try:
                os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
                self._process_events(1.0)
                
                loop = GLib.MainLoop()
                surface_holder = [None]
                
                def callback(obj, result, l):
                    try:
                        surface_holder[0] = self.view.get_snapshot_finish(result)
                    except Exception as e:
                        print(f"Screenshot error: {e}")
                    l.quit()
                
                GLib.idle_add(lambda: self.view.get_snapshot(
                    WebKit.SnapshotRegion.VISIBLE,
                    WebKit.SnapshotOptions.NONE,
                    None,
                    callback,
                    loop
                ) and False)
                
                GLib.timeout_add(5000, lambda: loop.quit())
                loop.run()
                
                surface = surface_holder[0]
                if surface:
                    surface.write_to_png(path)
                    return path
            except Exception as e:
                print(f"Screenshot error: {e}")
            return path

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
    print("\nRun with: python -m browser_mcp")


if __name__ == "__main__":
    main()
