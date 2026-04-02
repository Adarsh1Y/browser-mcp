import threading
import time
import json
import os
import subprocess
import tempfile
import random

try:
    import gi
    gi.require_version('WebKit2', '4.1')
    from gi.repository import WebKit2 as WebKit, GLib
    WEBKIT_AVAILABLE = True
except (ImportError, ValueError) as e:
    WEBKIT_AVAILABLE = False


class WebKitBrowser:
    def __init__(self, width: int = 1024, height: int = 768, auto_screenshot: bool = False, human_speed: str = "normal"):
        if not WEBKIT_AVAILABLE:
            raise ImportError("WebKitGTK not available")
        
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self._result_ready = threading.Event()
        self._js_result = None
        self._snapshot_ready = threading.Event()
        self._snapshot_surface = None
        self._current_url = None
        self._auto_screenshot = auto_screenshot
        self._last_screenshot_path = None
        self._console_messages = []
        
        # Human behavior settings
        self._human_speed = human_speed
        self._speed_config = {
            "subtle": {"keystroke_ms": (30, 70), "pause_sec": (0.5, 1.5), "think_sec": (0.5, 1.5)},
            "normal": {"keystroke_ms": (80, 150), "pause_sec": (1.0, 2.5), "think_sec": (1.0, 3.0)},
            "extreme": {"keystroke_ms": (150, 250), "pause_sec": (2.0, 4.0), "think_sec": (2.0, 5.0)},
        }
        
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

    def _on_console_message(self, view, message, line, source_id):
        self._console_messages.append({
            "message": message,
            "line": line,
            "source": source_id
        })
        return True

    def get_console_messages(self) -> list:
        """Get all captured console messages."""
        return self._console_messages.copy()

    def clear_console(self):
        """Clear console message buffer."""
        self._console_messages.clear()

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

    def close(self):
        """Close the browser and cleanup resources."""
        try:
            self._window.destroy()
        except Exception:
            pass

    def ping(self) -> bool:
        """Check if browser is still alive."""
        try:
            return self._window.get_visible() or self.view.get_uri() is not None
        except Exception:
            return False

    def click_at(self, x: int, y: int):
        """Click at specific X,Y coordinates."""
        script = f"""
        (function() {{
            var element = document.elementFromPoint({x}, {y});
            if(element) {{
                element.click();
                return 'clicked at ' + {x} + ',' + {y};
            }}
            return 'no element at position';
        }})()
        """
        return self._execute_js(script)

    def hover(self, selector: str, is_xpath: bool = False):
        """Hover over an element."""
        if is_xpath:
            script = f"(function(){{var el=document.evaluate('{selector}',document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue;if(el){{el.dispatchEvent(new MouseEvent('mouseenter',{{bubbles:true}}));el.dispatchEvent(new MouseEvent('mouseover',{{bubbles:true}}));return'hovered';}}return'not found';}})()"
        else:
            script = f"(function(){{var el=document.querySelector('{selector}');if(el){{el.dispatchEvent(new MouseEvent('mouseenter',{{bubbles:true}}));el.dispatchEvent(new MouseEvent('mouseover',{{bubbles:true}}));return'hovered';}}return'not found';}})()"
        return self._execute_js(script)

    def click_containing(self, text: str):
        """Click element containing specific text."""
        escaped_text = text.replace("'", "\\'")
        script = f"""
        (function() {{
            var el = Array.from(document.querySelectorAll('a, button, [role=\"button\"], input[type=\"submit\"], label'))
                .find(e => e.textContent.includes('{escaped_text}'));
            if (el) {{
                el.click();
                return 'clicked: ' + el.tagName;
            }}
            var allEls = document.querySelectorAll('*');
            for (var e of allEls) {{
                if (e.textContent.includes('{escaped_text}') && (e.click || e.onclick)) {{
                    e.click();
                    return 'clicked: ' + e.tagName;
                }}
            }}
            return 'not found';
        }})()
        """
        return self._execute_js(script)

    def click_nth(self, selector: str, n: int):
        """Click the nth element matching selector."""
        script = f"(function(){{var els=document.querySelectorAll('{selector}');if(els[{n-1}]{{els[{n-1}].click();return'clicked ' + ({n});}}return'not found';}})()"
        return self._execute_js(script)

    # ========== Human-Like Behavior Methods ==========

    def _get_timing(self, timing_type: str) -> tuple:
        """Get timing values based on human speed setting."""
        config = self._speed_config.get(self._human_speed, self._speed_config["normal"])
        timing = config.get(timing_type, config["pause_sec"])
        return timing

    def _random_delay(self, timing_type: str):
        """Sleep for a random duration based on timing type."""
        timing = self._get_timing(timing_type)
        delay = random.uniform(timing[0], timing[1])
        time.sleep(delay)

    def type_slow(self, selector: str, text: str, speed: str = None) -> str:
        """Type text with human-like keystroke timing."""
        if speed is None:
            speed = self._human_speed
        
        speed_config = self._speed_config.get(speed, self._speed_config["normal"])
        keystroke_range = speed_config["keystroke_ms"]
        
        # Clear field first
        self._execute_js(f"document.querySelector('{selector}').value = '';")
        
        for char in text:
            # Type each character with random delay
            delay = random.uniform(keystroke_range[0], keystroke_range[1]) / 1000.0
            time.sleep(delay)
            
            # Append character using JS
            escaped_char = char.replace("'", "\\'")
            self._execute_js(f"""
                var el = document.querySelector('{selector}');
                el.value += '{escaped_char}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
            """)
        
        # Trigger change event
        self._execute_js(f"document.querySelector('{selector}').dispatchEvent(new Event('change', {{bubbles: true}}));")
        
        return f"typed {len(text)} characters"

    def move_to(self, selector: str, duration: float = 0.5) -> str:
        """Move mouse smoothly to element (simulated with hover)."""
        result = self.hover(selector)
        # Add slight delay after hovering
        time.sleep(duration)
        return result

    def scroll_slow(self, direction: str = "down", distance: int = 300, speed: str = None) -> str:
        """Scroll smoothly with human-like timing."""
        if speed is None:
            speed = self._human_speed
        
        speed_config = self._speed_config.get(speed, self._speed_config["normal"])
        pause_range = speed_config["pause_sec"]
        
        # Convert direction to scroll amount
        direction_map = {
            "down": distance,
            "up": -distance,
            "top": -999999,
            "bottom": 999999,
            "down-half": lambda: self._execute_js("window.scrollBy(0, window.innerHeight / 2)"),
            "up-half": lambda: self._execute_js("window.scrollBy(0, -window.innerHeight / 2)"),
        }
        
        if direction in ["top", "bottom"]:
            self._execute_js(f"window.scrollTo(0, {direction_map[direction]})")
        elif direction in ["down-half", "up-half"]:
            direction_map[direction]()
        else:
            # Smooth scroll in steps
            steps = 5
            step_size = distance // steps
            for _ in range(steps):
                self._execute_js(f"window.scrollBy(0, {step_size})")
                time.sleep(random.uniform(pause_range[0], pause_range[1]) / steps)
        
        return f"scrolled {direction}"

    def random_pause(self, min_sec: float = None, max_sec: float = None) -> str:
        """Pause for a random duration (like human thinking)."""
        if min_sec is None or max_sec is None:
            think_range = self._get_timing("think_sec")
            min_sec = think_range[0]
            max_sec = think_range[1]
        
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        return f"paused for {delay:.2f}s"

    def hesitant_click(self, selector: str, is_xpath: bool = False) -> str:
        """Click with hesitation - pause before clicking."""
        # First hover/move to element
        self.move_to(selector, duration=0.3)
        # Random pause before clicking (hesitation)
        self._random_delay("think_sec")
        # Now click
        return self.click(selector, is_xpath)

    def scan_page(self) -> str:
        """Simulate human scanning the page - scroll a bit up and down."""
        # Quick scroll down
        self.scroll_slow("down", 200, speed="subtle")
        time.sleep(0.5)
        # Quick scroll back up
        self.scroll_slow("up", 200, speed="subtle")
        return "scanned page"

    # ========== Enhanced Existing Methods with Human Mode ==========

    def fill(self, selector: str, value: str, human: bool = True) -> str:
        """Fill input field with optional human-like typing."""
        if human:
            return self.type_slow(selector, value)
        else:
            # Original fast fill
            safe_value = value.replace("'", "\\'")
            script = f"(function(){{var el=document.querySelector('{selector}');if(el){{el.value='{safe_value}';el.dispatchEvent(new Event('input',{{bubbles:true}}));el.dispatchEvent(new Event('change',{{bubbles:true}}));return'filled';}}return'not found';}})()"
            return self._execute_js(script)

    def click(self, selector: str, is_xpath: bool = False, human: bool = True) -> str:
        """Click element with optional human-like behavior."""
        if human:
            return self.hesitant_click(selector, is_xpath)
        else:
            # Original fast click
            if is_xpath:
                script = f"(function() {{var el=document.evaluate('{selector}',document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue;if(el){{el.click();return'clicked';}}return'not found';}})()"
            else:
                script = f"(function() {{var el=document.querySelector('{selector}');if(el){{el.click();return'clicked';}}return'not found';}})()"
            return self._execute_js(script)

    def navigate(self, url: str, wait: float = 2.0, human: bool = True) -> dict:
        """Navigate to URL with optional human-like reading pause."""
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
            
            if human:
                # Add reading pause after page load
                self._random_delay("think_sec")
            
            if self._auto_screenshot:
                self._last_screenshot_path = self._screenshot_gtk("/tmp/auto_screenshot.png", False)
            
            return {
                "url": self.view.get_uri() or url,
                "title": self.view.get_title() or ""
            }

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

    def set_auto_screenshot(self, enabled: bool):
        """Enable or disable auto-screenshot on navigation."""
        self._auto_screenshot = enabled

    def get_last_screenshot(self) -> str:
        """Get path to the last auto-screenshot."""
        return self._last_screenshot_path or ""

    def repl(self, script: str) -> str:
        """Execute JavaScript and return pretty-printed result."""
        result = self._execute_js(script)
        if result is None:
            return "null"
        try:
            parsed = json.loads(result)
            return json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError):
            return str(result) if result else "null"

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
