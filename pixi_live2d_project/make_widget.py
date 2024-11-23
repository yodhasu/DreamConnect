import webview
import screeninfo

# Get screen width (you can adjust for your screen resolution)
screen = screeninfo.get_monitors()[0]
screen_width = screen.width

# Set the window to appear on the right side of the screen
window_width = 600  # Width of your window (adjust as needed)
x_position = screen_width - window_width  # Position it at the far right
html_file = "index.html"

# Create the WebView window
webview.create_window("Live2D Viewer", html_file, width=600, height=800, transparent=False, frameless=True, draggable=True, x = x_position, y=100)
webview.start()