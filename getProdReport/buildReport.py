from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import requests
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def fill_word_template(template_path, output_path, context, img_context=None):
    # Load your .docx template
    doc = DocxTemplate(template_path)

    # Context is a dictionary with your placeholders and their replacements
    # For example, context = {'name': 'John Doe', 'date': '01/01/2024'}

    # If you have images in your template, you can use the following code to replace them
    if img_context:
        for key, value in img_context.items():
            img = InlineImage(doc, value['path'], width=Mm(value['width']))
            context[key] = img

    # Render the template with the context
    doc.render(context)

    # Save the generated document
    doc.save(output_path)


def convert_docx_to_pdf_with_api2pdf(api_key, docx_url, output_url, pdf_filename):
    # Endpoint for converting a file to PDF
    url = "https://v2.api2pdf.com/libreoffice/any-to-pdf"


    # Prepare the headers
    headers = {
        "Authorization": api_key
    }
    body = {
        "url": docx_url,
        "inline": False,
        "fileName": pdf_filename,
        "extraHTTPHeaders": {},
        "useCustomStorage": True,
        "storage": {
            "method": "PUT",
            "url": output_url,
            "extraHTTPHeaders": {}
        }
    }

    # Send the request
    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        # If the request was successful, write the PDF to a file
        return True
    else:
        # If the request failed, print the error
        print("PDF conversion failed:", response.text)
        return False
    

def convert_docx_to_pdf_with_apyhub(api_key, docx_url, output_url, pdf_filename):
    # Endpoint for converting a file to PDF
    api_url = "https://api.apyhub.com/convert/word-url/pdf-url"

    # Prepare the headers
    headers = {
        'Content-Type': "application/json",
        'apy-token':api_key,
    }

    # query parameters
    query_params = {
        'output':pdf_filename,
    }

    body = {
        'url':docx_url,
    }

    # Send the request
    try:
        response = requests.post(api_url, headers=headers, params=query_params, json=body)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error converting docx to pdf: {e}")
        return False

    if response.status_code == 200:
        # If the request was successful, get data from the response
        data = response.json()
        logger.info(f"PDF conversion successful: {data.get('data', {})}")
        # return the given url
        return data.get('data', {})
    else:
        # If the request failed, print the error
        print("PDF conversion failed:", response.text)
        return False