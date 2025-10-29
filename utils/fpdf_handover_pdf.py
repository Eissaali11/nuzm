import qrcode
import base64
import io
import os
from urllib.request import pathname2url
from flask import render_template, current_app
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def generate_handover_report_pdf_weasyprint(handover):
    """
    Generates a PDF report using WeasyPrint with a custom font and base64-encoded images.
    """
    # Initialize font configuration
    font_config = FontConfiguration()

    try:
        # Helper function to convert image file to base64
        def image_to_base64(file_path):
            """Convert image file to base64 data URL"""
            if not file_path or file_path == 'None' or file_path == 'null':
                return None
            
            # Try multiple possible locations for the image
            possible_paths = [
                file_path,
                os.path.join(current_app.root_path, file_path),
                os.path.join(current_app.root_path, 'static', file_path),
                os.path.join(current_app.root_path, 'uploads', file_path),
                os.path.join(current_app.root_path, 'static', 'uploads', file_path),
                os.path.join(current_app.static_folder, file_path),
                os.path.join(current_app.static_folder, 'uploads', file_path)
            ]
            
            # Log the paths being tried
            current_app.logger.info(f"Looking for image: {file_path}")
            
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        current_app.logger.info(f"Found image at: {path}")
                        with open(path, 'rb') as img_file:
                            img_data = img_file.read()
                            img_b64 = base64.b64encode(img_data).decode('utf-8')
                            # Detect image type
                            ext = os.path.splitext(path)[1].lower()
                            mime_type = {
                                '.png': 'image/png',
                                '.jpg': 'image/jpeg',
                                '.jpeg': 'image/jpeg',
                                '.gif': 'image/gif',
                                '.bmp': 'image/bmp',
                                '.webp': 'image/webp'
                            }.get(ext, 'image/png')
                            return f"data:{mime_type};base64,{img_b64}"
                    except Exception as e:
                        current_app.logger.warning(f"Failed to read image {path}: {e}")
                        continue
            
            current_app.logger.error(f"Image not found in any location: {file_path}. Tried paths: {possible_paths}")
            return None

        # Convert all image paths to base64
        damage_diagram_b64 = None
        if handover.damage_diagram_path:
            damage_diagram_b64 = image_to_base64(handover.damage_diagram_path)
        
        driver_signature_b64 = None
        if handover.driver_signature_path:
            driver_signature_b64 = image_to_base64(handover.driver_signature_path)
        
        supervisor_signature_b64 = None
        if handover.supervisor_signature_path:
            supervisor_signature_b64 = image_to_base64(handover.supervisor_signature_path)
        
        movement_officer_signature_b64 = None
        if hasattr(handover, 'movement_officer_signature_path') and handover.movement_officer_signature_path:
            movement_officer_signature_b64 = image_to_base64(handover.movement_officer_signature_path)
        
        # Convert handover images to base64
        handover_images_b64 = []
        if handover.images:
            for img in handover.images:
                img_b64 = image_to_base64(img.file_path)
                if img_b64:
                    handover_images_b64.append({
                        'file_path': img_b64,
                        'file_description': img.file_description
                    })

        # Generate QR code if a form link is provided
        qr_code_url = None
        if handover.form_link:
            qr_img = qrcode.make(handover.form_link)
            buffered = io.BytesIO()
            qr_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            qr_code_url = f"data:image/png;base64,{img_str}"
        
        # Generate QR code for second form link if provided
        qr_code_url_2 = None
        if handover.form_link_2:
            qr_img_2 = qrcode.make(handover.form_link_2)
            buffered_2 = io.BytesIO()
            qr_img_2.save(buffered_2, format="PNG")
            img_str_2 = base64.b64encode(buffered_2.getvalue()).decode('utf-8')
            qr_code_url_2 = f"data:image/png;base64,{img_str_2}"

        # Render the HTML template with base64 images
        html_string = render_template(
            'vehicles/handover_report.html',
            handover=handover,
            qr_code_url=qr_code_url,
            qr_code_url_2=qr_code_url_2,
            damage_diagram_b64=damage_diagram_b64,
            driver_signature_b64=driver_signature_b64,
            supervisor_signature_b64=supervisor_signature_b64,
            movement_officer_signature_b64=movement_officer_signature_b64,
            handover_images_b64=handover_images_b64
        )

        # Locate static folder and pick a font
        static_folder = os.path.join(current_app.root_path, 'static')
        font_options = [
            ('beIN-Normal', 'beIN-Normal.ttf'),
            ('Cairo',      'Cairo.ttf'),
        ]
        selected_family = 'Arial'
        selected_path = None
        for family, filename in font_options:
            fp = os.path.join(static_folder, 'fonts', filename)
            if os.path.exists(fp):
                selected_family = family
                selected_path = fp
                break

        # Build @font-face CSS
        if selected_path:
            font_url = f"file://{pathname2url(selected_path)}"
            font_css = CSS(
                string=f'''@font-face {{
    font-family: "{selected_family}";
    src: url("{font_url}");
}}
body {{
    font-family: "{selected_family}";
}}''',
                font_config=font_config
            )
        else:
            font_css = CSS(
                string="body { font-family: Arial, sans-serif; }",
                font_config=font_config
            )

        # Create HTML object with base_url for static assets
        static_folder = os.path.join(current_app.root_path, 'static')
        html = HTML(string=html_string, base_url=static_folder)

        # Write PDF
        pdf_buffer = io.BytesIO()
        html.write_pdf(
            pdf_buffer,
            stylesheets=[font_css],
            font_config=font_config
        )
        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        current_app.logger.exception("Error generating handover report PDF")
        raise
