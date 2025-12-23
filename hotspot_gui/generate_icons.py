#!/usr/bin/env python3
"""
Generate PWA icons for Hotspot Manager
"""
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available, creating placeholder icons")

def create_gradient_icon(size):
    """Create a gradient icon with hotspot symbol"""
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)

    # Create gradient background (purple to blue)
    for y in range(size):
        r = int(102 + (118 - 102) * y / size)
        g = int(126 + (75 - 126) * y / size)
        b = int(234 + (162 - 234) * y / size)
        draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b))

    # Draw hotspot symbol (WiFi waves)
    center_x, center_y = size // 2, size // 2

    # Draw center dot
    dot_size = size // 10
    draw.ellipse([
        center_x - dot_size,
        center_y - dot_size,
        center_x + dot_size,
        center_y + dot_size
    ], fill='white')

    # Draw WiFi arcs
    arc_width = size // 20
    for i in range(1, 4):
        arc_radius = size // 6 * i
        draw.arc([
            center_x - arc_radius,
            center_y - arc_radius,
            center_x + arc_radius,
            center_y + arc_radius
        ], start=-45, end=45, fill='white', width=arc_width)

    return img

def create_simple_icon(size):
    """Create a simple colored square icon (fallback)"""
    img = Image.new('RGB', (size, size), color=(102, 126, 234))
    draw = ImageDraw.Draw(img)

    # Draw a simple "H" for Hotspot
    padding = size // 4
    line_width = size // 10

    # Left vertical line
    draw.rectangle([
        padding,
        padding,
        padding + line_width,
        size - padding
    ], fill='white')

    # Right vertical line
    draw.rectangle([
        size - padding - line_width,
        padding,
        size - padding,
        size - padding
    ], fill='white')

    # Horizontal middle line
    draw.rectangle([
        padding,
        size // 2 - line_width // 2,
        size - padding,
        size // 2 + line_width // 2
    ], fill='white')

    return img

if __name__ == '__main__':
    import os

    icon_dir = '/data/data/com.termux/files/home/hotspot_gui'

    if PIL_AVAILABLE:
        print("Generating icons with PIL...")

        # Generate 192x192 icon
        print("Creating 192x192 icon...")
        icon_192 = create_gradient_icon(192)
        icon_192.save(os.path.join(icon_dir, 'icon-192.png'), 'PNG')

        # Generate 512x512 icon
        print("Creating 512x512 icon...")
        icon_512 = create_gradient_icon(512)
        icon_512.save(os.path.join(icon_dir, 'icon-512.png'), 'PNG')

        print("✓ Icons generated successfully!")
    else:
        # Create minimal placeholder PNG using ImageDraw fallback
        print("Creating basic icons without PIL...")
        try:
            from PIL import Image, ImageDraw

            icon_192 = create_simple_icon(192)
            icon_192.save(os.path.join(icon_dir, 'icon-192.png'), 'PNG')

            icon_512 = create_simple_icon(512)
            icon_512.save(os.path.join(icon_dir, 'icon-512.png'), 'PNG')

            print("✓ Basic icons generated!")
        except:
            print("✗ Cannot create icons - PIL not available")
            print("  Run: pkg install python-pillow")
