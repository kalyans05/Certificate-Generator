from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

def generate_certificate(template_path, name, usn, coords, font_size,font_style,max_width,text_color):
    try:
        # Load the certificate template
        image = Image.open(template_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template not found at {template_path}")
    except UnidentifiedImageError:
        raise ValueError("File is not a valid image format")

    draw = ImageDraw.Draw(image)
    
    # Define the text to add
    text = f"{name} ({usn})"
    
    try:
        font = ImageFont.truetype(font_style, round(1.333*font_size))
    except IOError:
        raise IOError("Font not found or cannot be loaded")

    # Calculate the bounding box of the text to center it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    
    # Adjust font size if text width exceeds max width
    while text_width > max_width:
        font_size -= 1
        font = ImageFont.truetype(font_style, round(1.333*font_size))
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
    # Calculate the bounding box of the text to center it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Adjust the coordinates to center the text
    x = coords[0] - text_width // 2
    y = coords[1] - text_height // 2

    # Add the text to the image
    draw.text((x, y), text, fill="#"+text_color, font=font)
    
    # Save the result as a PDF
    output_path = f"{usn}.pdf"
    image.save(output_path, format="PDF")
    
    return output_path

