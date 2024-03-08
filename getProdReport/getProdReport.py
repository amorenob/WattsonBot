import os
import requests
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
#from jinja2 import Environment, FileSystemLoader
#from weasyprint import HTML
import boto3
import random
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import math

# Create a dictionary mapping month numbers to names
month_names = {
    1: 'Ene',
    2: 'Feb',
    3: 'Mar',
    4: 'Abr',   
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Ago',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dic'
}

# Panels area
panels_area = {
    400: 2.0,
}

TEMP_DIR = '/tmp'

def getLocationImage(lat, lon, google_api_key):
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom=14&size=310x310&maptype=roadmap&markers=color:red%7C{lat},{lon}&key={google_api_key}"
    response = requests.get(url)
    return response

def getLocationInfo(lat, lon, google_api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={google_api_key}"
    response = requests.get(url)
    return response

def savePdfInS3(pdf, bucket, key):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=pdf, ContentType='application/pdf')
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def saveDocxInS3(docx, bucket, key):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=docx, ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def getReportKey(userId, conversarionId, extension):
    ramdom_int = random.randint(0, 1000000)
    return f"{userId}/{conversarionId}/reports/{ramdom_int}.{extension}"

def getGetterSignedUrl(bucket, key):
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key})
    return url

def getUploaderSignedUrl(bucket, key):
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': key})
    return url

def calculateOptimalTilt(lat):
    lat = float(lat)
    # Calculate the optimal tilt
    tilt = lat - 2.5
    return round(tilt, 2)

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

def renderHtmlToPdf(html_template, report_data, output_path):
    # Render the template with the data
    # Create a Jinja2 environment
    #env = Environment(loader=FileSystemLoader('.'))
    #template = env.get_template(html_template)
    #html = template.render(report_data)

    # Save the rendered HTML to a file
    # Crear el PDF

    # Use a file:// URL as the base URL
    base_url = 'file://'
    
    #HTML(string=html, base_url=base_url).write_pdf(output_path)
    return None


def lambda_handler(event, context):

    # Get query parameters
    lat = event['queryStringParameters']['lat']
    lon = event['queryStringParameters']['lon']
    system_capacity = event['queryStringParameters']['system_capacity']
    avg_daily_consumption = float(event['queryStringParameters']['avgDailyConsumption'])
    panels_capacity = float(event['queryStringParameters']['panelsCapacity'])
    userId = event['queryStringParameters']['userId']
    conversationId = event['queryStringParameters']['conversationId']


    nrel_api_key = os.environ['NREL_API_KEY']
    google_api_key = os.environ['GOOGLE_API_KEY']
    api2pdf_api_key = os.environ['API2PDF_API_KEY']

    # Get the location image
    location_image = getLocationImage(lat, lon, google_api_key)
    if location_image.status_code != 200:
        return {
            'statusCode': 500,
            'body': 'Error calling Google API'
        }
    else:
        location_image = location_image.content

    # get the location info
    location_info = getLocationInfo(lat, lon, google_api_key)
    if location_info.status_code != 200:
        return {
            'statusCode': 500,
            'body': 'Error calling Google API'
        }
    else:
        location_info = location_info.json()
    
    address = location_info['results'][0]['formatted_address']


    #save the image to a file
    location_file = os.path.join(TEMP_DIR, 'location_image.png')
    with open(location_file, 'wb') as f:
        f.write(location_image)

    # Calculate the optimal inclination
    tilt = calculateOptimalTilt(lat)
    # Call NREL API
    url = f"https://developer.nrel.gov/api/pvwatts/v8.json?api_key={nrel_api_key}&lat={lat}&lon={lon}&system_capacity={system_capacity}&azimuth=180&tilt={tilt}&array_type=1&module_type=1&losses=20"

    # Get the response
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': 500,
            'body': 'Error calling NREL API'
        }
    else:
        data = response.json()

    # Convert the data to a list of dictionaries
    ac_monthly = data['outputs']['ac_monthly']
    hsp = data['outputs']['solrad_annual']
    # Create a list of month names
    months = [month_names[i+1] for i in range(12)]

    # Plots dc monthly production with seaborn
    plt.figure(figsize=(10, 5))

    # Create a color map
    min_val = min(ac_monthly)
    max_val = max(ac_monthly)
    norm = plt.Normalize(min_val*0.4, max_val*1.5)  # Adjust the range here
    colors = cm.Oranges(norm(ac_monthly))

    # Create a bar plot
    plt.bar(months, ac_monthly, width=0.5)
    # Get the current Axes instance
    ax = plt.gca()
    # Manually set the color of each bar
    for i, bar in enumerate(ax.patches):
        bar.set_color(colors[i])

    # Add labels to the axes
    plt.xlabel('Mes')
    plt.ylabel('kWh')
    plt.title('Produccion mensual')

    # Tilt the month names on the x-axis
    plt.xticks(rotation=45)

    # Save plot to file
    prof_file = os.path.join(TEMP_DIR, 'monthly_production.png')
    plt.savefig(prof_file)

    # calculate the anual production and consumption
    anual_production =  math.floor(sum(ac_monthly))
    anual_consumption = math.ceil(avg_daily_consumption * 365)
    # percentage of annual saves
    savings_percentage = round(anual_production / anual_consumption * 100, 1)
    n_panels = int(float(system_capacity)//(panels_capacity/1000))
    req_area = math.ceil(n_panels * panels_area[panels_capacity])

    # Fill the word template
    # Define paths and context
    template_path = 'wattsonReportTemplate.docx'
    output_path = os.path.join(TEMP_DIR, 'prodReport.docx')
    template_context = {
        'nombreProyecto': 'Produccion de energia solar',
        'dirProyecto': address,
        'potenciaInstalada': system_capacity,
        'nPaneles': n_panels,
        'horasSolaresPico': round(hsp, 2),
        'perdidas':20,
        'inclinacion': tilt,
        'orientacion': 180,
        'prodAnual': anual_production,
        'consumoAnual': anual_consumption,
        'ahorroAnual': savings_percentage,
        'areaRequerida': req_area,
    }

    img_context = {
        'imglUbicacion': {'path': location_file, 'width': 42},
        'imglProduccion': {'path': prof_file, 'width': 130}
    }

    fill_word_template(template_path, output_path, template_context, img_context)

    # Save report to S3
    bucket = os.environ['UploadBucket']
    #key = getReportKey(userId, conversationId, 'pdf')
    docx_key = getReportKey(userId, conversationId, 'docx')
    docx_url = saveDocxInS3(open(output_path, 'rb'), bucket, docx_key)
    docx_signed_url = getGetterSignedUrl(bucket, docx_key)

    # Convert the docx to pdf
    pdf_key = docx_key.replace('docx', 'pdf')
    pdf_filename = pdf_key.split('/')[-1]
    pdf_signed_url = getUploaderSignedUrl(bucket, pdf_key)
    pdf_url = convert_docx_to_pdf_with_api2pdf(api2pdf_api_key, docx_signed_url, pdf_signed_url, pdf_filename)

    if not pdf_url:
        return {
            'statusCode': 500,
            'body': 'Error converting docx to pdf'
        }
    
    # Return the signed url
    pdf_signed_url = getGetterSignedUrl(bucket, pdf_key)
    return {
        'statusCode': 200,
        'body': json.dumps({'pdfUrl': pdf_signed_url})
    }
