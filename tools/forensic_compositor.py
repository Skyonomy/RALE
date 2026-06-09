import io
import base64
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Dict

logger = logging.getLogger(__name__)

class ForensicCompositor:
    """
    The Forensic Compositor: Deterministic pixel-level data grounding.
    Draws coordinate markers on the map for the Teacher View and 
    performs digital redaction for the Student View.
    """

    @staticmethod
    def redact_student_map(raw_binary: bytes, vision_result: Dict) -> bytes:
        """
        Removes/Redacts the text labels from the original image to create a clean 'Student View'.
        Samples surrounding pixels to 'generatively heal' the map floor.
        """
        try:
            img = Image.open(io.BytesIO(raw_binary)).convert("RGB")
            draw = ImageDraw.Draw(img)
            width, height = img.size
            labels = vision_result.get('labels', [])

            for label in labels:
                if all(k in label for k in ('xmin', 'ymin', 'xmax', 'ymax')):
                    # Use a slightly larger box for redaction to ensure text edges are gone
                    buffer = 5
                    xmin_px = max(0, ((float(label['xmin']) - buffer) / 1000.0) * width)
                    ymin_px = max(0, ((float(label['ymin']) - buffer) / 1000.0) * height)
                    xmax_px = min(width, ((float(label['xmax']) + buffer) / 1000.0) * width)
                    ymax_px = min(height, ((float(label['ymax']) + buffer) / 1000.0) * height)

                    # --- PIXEL-PATCH REDACTION ---
                    # Sample the pixel just outside the top-left corner to get the floor color
                    sample_x = max(0, int(xmin_px) - 2)
                    sample_y = max(0, int(ymin_px) - 2)
                    bg_color = img.getpixel((sample_x, sample_y))

                    # Fill the bounding box with the sampled floor color
                    draw.rectangle([xmin_px, ymin_px, xmax_px, ymax_px], fill=bg_color)

            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return buffered.getvalue()
        except Exception as e:
            logger.error(f"Redaction Error: {e}")
            return raw_binary

    @staticmethod
    def draw_compass_overlay(raw_binary: bytes) -> bytes:
        """
        Draws a crisp, professional, unhallucinated cartographic compass rose overlay 
        in the top-right corner of the map. This is shared between both Student and Teacher views.
        """
        try:
            img = Image.open(io.BytesIO(raw_binary)).convert("RGBA")
            width, height = img.size
            if width < 100 or height < 100:
                logger.info("Image too small for compass overlay (skipping).")
                img = img.convert("RGB")
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return buffered.getvalue()
                
            draw = ImageDraw.Draw(img)
            
            # Position the compass rose in the top-right corner
            cx, cy = int(width * 0.92), int(height * 0.08)
            radius = int(width * 0.04) # e.g. 40px radius on 1000px width
            
            # Try to load a clean bold font for N/S/E/W labels
            font = None
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "arial.ttf"
            ]
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, 14)
                    break
                except:
                    continue
            if not font:
                font = ImageFont.load_default()
                
            # Outer Ring
            ring_color = (40, 50, 60, 220)
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=ring_color, width=2)
            # Inner small ring
            draw.ellipse([cx - int(radius*0.3), cy - int(radius*0.3), cx + int(radius*0.3), cy + int(radius*0.3)], outline=ring_color, width=1)
            
            # North-South, East-West Crosshairs
            draw.line([(cx, cy - radius), (cx, cy + radius)], fill=ring_color, width=1)
            draw.line([(cx - radius, cy), (cx + radius, cy)], fill=ring_color, width=1)
            
            # Draw North Arrow (Gilded/Teal pointer)
            draw.polygon([(cx, cy), (cx - 6, cy), (cx, cy - radius)], fill=(0, 200, 200, 255))
            draw.polygon([(cx, cy), (cx + 6, cy), (cx, cy - radius)], fill=(0, 255, 255, 255))
            # South Needle
            draw.polygon([(cx, cy), (cx - 5, cy), (cx, cy + int(radius*0.8))], fill=(150, 150, 150, 255))
            draw.polygon([(cx, cy), (cx + 5, cy), (cx, cy + int(radius*0.8))], fill=(200, 200, 200, 255))
            
            # Draw labels: N, S, E, W
            # Draw 'N' above
            draw.text((cx - 5, cy - radius - 18), "N", fill=(0, 255, 200, 255), font=font)
            # Draw 'S' below
            draw.text((cx - 5, cy + radius + 4), "S", fill=ring_color, font=font)
            # Draw 'E' right
            draw.text((cx + radius + 6, cy - 7), "E", fill=ring_color, font=font)
            # Draw 'W' left
            draw.text((cx - radius - 16, cy - 7), "W", fill=ring_color, font=font)
            
            # Center cap
            draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 255, 255), outline=ring_color)
            
            img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return buffered.getvalue()
        except Exception as e:
            logger.error(f"Compass Overlay Error: {e}")
            return raw_binary

    @staticmethod
    def composite_teacher_map(raw_binary: bytes, vision_result: Dict) -> str:
        """
        Draws numbered pins on the image based on extracted coordinates.
        Returns a base64 encoded string of the final image.
        """
        try:
            img = Image.open(io.BytesIO(raw_binary)).convert("RGBA")
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw_overlay = ImageDraw.Draw(overlay)
            
            # 1. Improved Font Selection for Docker (Linux Slim)
            font = None
            small_font = None
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "arial.ttf" # Fallback for local dev
            ]
            
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, 40)
                    small_font = ImageFont.truetype(path, 16)
                    break
                except:
                    continue
            
            if not font:
                logger.warning("No system font found, falling back to default (might be small).")
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
                
            width, height = img.size
            labels = vision_result.get('labels', [])
            
            for label in labels:
                # Optional: Draw Bounding Box if present
                if all(k in label for k in ('xmin', 'ymin', 'xmax', 'ymax')):
                    xmin_px = (float(label['xmin']) / 1000.0) * width
                    ymin_px = (float(label['ymin']) / 1000.0) * height
                    xmax_px = (float(label['xmax']) / 1000.0) * width
                    ymax_px = (float(label['ymax']) / 1000.0) * height
                    
                    # 1 & 2. Sci-fi HUD corner brackets + Translucent fill
                    c_color = (0, 255, 100, 255) # Bright green/teal
                    fill_color = (0, 255, 100, 25) # Subtle 10% opacity fill
                    line_w = 4
                    corner_length = min(40.0, (xmax_px - xmin_px) * 0.25, (ymax_px - ymin_px) * 0.25)
                    
                    draw_overlay.rectangle(
                        [xmin_px, ymin_px, xmax_px, ymax_px],
                        fill=fill_color,
                        outline=c_color,
                        width=3
                    )
                    # Top-Left
                    draw_overlay.line([(xmin_px, ymin_px + corner_length), (xmin_px, ymin_px), (xmin_px + corner_length, ymin_px)], fill=c_color, width=line_w)
                    # Top-Right
                    draw_overlay.line([(xmax_px - corner_length, ymin_px), (xmax_px, ymin_px), (xmax_px, ymin_px + corner_length)], fill=c_color, width=line_w)
                    # Bottom-Left
                    draw_overlay.line([(xmin_px, ymax_px - corner_length), (xmin_px, ymax_px), (xmin_px + corner_length, ymax_px)], fill=c_color, width=line_w)
                    # Bottom-Right
                    draw_overlay.line([(xmax_px - corner_length, ymax_px), (xmax_px, ymax_px), (xmax_px, ymax_px - corner_length)], fill=c_color, width=line_w)

                    # Optional debug faint box
                    # draw_overlay.rectangle([xmin_px, ymin_px, xmax_px, ymax_px], outline=(0, 255, 100, 50), width=1)
            
                # 2. Coordinate Clamping (for the pin)
                x_pct = max(20, min(980, float(label.get('x', 500))))
                y_pct = max(20, min(980, float(label.get('y', 500))))
                
                x_px = (x_pct / 1000.0) * width
                y_px = (y_pct / 1000.0) * height
                
                # 3. Draw calculated centre crosshair
                ch_size = 20
                ch_color = (0, 255, 255, 255) # Cyan
                draw_overlay.line([(x_px - ch_size, y_px), (x_px + ch_size, y_px)], fill=ch_color, width=3)
                draw_overlay.line([(x_px, y_px - ch_size), (x_px, y_px + ch_size)], fill=ch_color, width=3)
                draw_overlay.ellipse([x_px - 4, y_px - 4, x_px + 4, y_px + 4], fill=(255, 255, 255, 255))
                
                # 4. Draw small HUD label near anchor
                num_text = str(label.get('number', '?'))
                hud_text = f"[{num_text}] VALIDATED"
                
                try:
                    bbox = draw_overlay.textbbox((0, 0), hud_text, font=small_font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                except:
                    tw, th = 80, 15 # Guess
                
                pad = 4
                text_x = x_px + 10
                text_y = y_px + 10
                draw_overlay.rectangle(
                    [text_x - pad, text_y - pad, text_x + tw + pad, text_y + th + pad],
                    fill=(0, 20, 20, 200) # Dark translucent background
                )
                draw_overlay.text((text_x, text_y), hud_text, fill=(0, 255, 200, 255), font=small_font)
                
            img = Image.alpha_composite(img, overlay)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

        except Exception as e:
            logger.error(f"Compositor Error: {e}")
            return base64.b64encode(raw_binary).decode('utf-8')
