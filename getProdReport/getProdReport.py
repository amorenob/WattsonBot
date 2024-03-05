import os
import requests
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import boto3
import random
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

def getFileKey(userId, conversarionId):
    ramdom_int = random.randint(0, 1000000)
    return f"{userId}/{conversarionId}/reports/{ramdom_int}.pdf"

def getSignedUrl(bucket, key):
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key})
    return url


def lambda_handler(event, context):
    # TODO: Implement your function logic here
    # Get query parameters
    lat = event['queryStringParameters']['lat']
    lon = event['queryStringParameters']['lon']
    system_capacity = event['queryStringParameters']['system_capacity']
    userId = event['queryStringParameters']['userId']
    conversationId = event['queryStringParameters']['conversationId']

    nrel_api_key = os.environ['NREL_API_KEY']
    google_api_key = os.environ['GOOGLE_API_KEY']

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
    file_path = os.path.join(TEMP_DIR, 'location_image.png')
    with open(file_path, 'wb') as f:
        f.write(location_image)

    # Call NREL API
    url = f"https://developer.nrel.gov/api/pvwatts/v8.json?api_key={nrel_api_key}&lat={lat}&lon={lon}&system_capacity={system_capacity}&azimuth=180&tilt=0&array_type=1&module_type=1&losses=20"

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

    # Create a Jinja2 environment
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')

    report_data = {
        'nombreProyecto': 'Produccion de energia solar',
        'dirProyecto': address,
        'potenciaInstalada': system_capacity,
        'nPaneles': int(int(system_capacity)//0.4),
        'horasSolaresPico': round(hsp, 2),
        'perdidas':20,
        'inclinacion': 0,
        'orientacion': 180,
        'prodAnual': sum(ac_monthly),
        'consumoAnual': 10000,
        'ahorroAnual': 10000 - sum(ac_monthly),
        'areaRequerida': 100,
    }

    # Render the template with the data
    html = template.render(report_data)

    # Save the rendered HTML to a file
    # Crear el PDF

    # Use a file:// URL as the base URL
    base_url = 'file://'
    report_file = os.path.join(TEMP_DIR, 'informe_completo.pdf')
    HTML(string=html, base_url=base_url).write_pdf(report_file)

    # Save the pdf to S3
    bucket = os.environ['UploadBucket']
    key = getFileKey(userId, conversationId)
    pdf_url = savePdfInS3(open(report_file, 'rb'), bucket, key)

    signed_url = getSignedUrl(bucket, key)

    # Return a 200 response with the url of the PDF
    return {
        'statusCode': 200,
        'body': json.dumps(signed_url)
    }

