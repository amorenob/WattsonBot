"""
This script generates a production report for a solar energy system based on the provided parameters.
It calculates the annual solar energy production, potential savings, and generates a report in PDF format.

Author: Amoreno
"""

import os
import requests
import json
import math
from solarUtils import *
from s3Utils import saveDocxInS3, getGetterSignedUrl, getUploaderSignedUrl, getReportKey, getRandomPdfKey, changeMetadata
from buildReport import fill_word_template, convert_docx_to_pdf_with_api2pdf
import config
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def formatNumber2Decimals(number):
    return round(number, 2)

def formatNumberToCurrency(number):
    return f"${int(number):,}"

def lambda_handler(event, context):
    """
    Lambda function handler for generating a production report.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.

    Returns:
        dict: The response containing the PDF URL of the generated report.

    Raises:
        KeyError: If any required query parameter is missing in the event data.
        requests.exceptions.RequestException: If there is an error calling the Google API or NREL API.
        ValueError: If the response from the NREL API is not in the expected format.
        IOError: If there is an error saving or reading the location image or production image.
        RuntimeError: If there is an error filling the word template or converting the docx to pdf.

    """

    # Get query parameters
    lat = event['queryStringParameters']['lat']
    lon = event['queryStringParameters']['lon']
    system_capacity = float(event['queryStringParameters']['system_capacity'])
    avg_daily_consumption = float(event['queryStringParameters']['avgDailyConsumption'])
    panels_capacity = float(event['queryStringParameters']['panelsCapacity'])
    userId = event['queryStringParameters']['userId']
    conversationId = event['queryStringParameters']['conversationId']

    costPerKwh = float(event['queryStringParameters']['costPerKwh'])

    # Get the location image
    location_image = getLocationImage(lat, lon, config.GOOGLE_API_KEY)
    if location_image.status_code != 200:
        return {
            'statusCode': 500,
            'body': 'Error calling Google API'
        }
    else:
        location_image = location_image.content
    #save the image to a file
    location_img = os.path.join(config.TEMP_DIR, 'location_image.png')
    with open(location_img, 'wb') as f:
        f.write(location_image)



    # get the location info
    location_info = getLocationInfo(lat, lon, config.GOOGLE_API_KEY)
    if location_info.status_code != 200:
        return {
            'statusCode': 500,
            'body': 'Error calling Google API'
        }
    else:
        location_info = location_info.json()
    
    address = location_info['results'][0]['formatted_address']

    # Calculate the optimal inclination
    tilt = calculateOptimalTilt(lat)
    # Call NREL API
    url = f"https://developer.nrel.gov/api/pvwatts/v8.json?api_key={config.NREL_API_KEY}&lat={lat}&lon={lon}&system_capacity={system_capacity}&azimuth=180&tilt={0}&array_type=1&module_type=1&losses=20"

    # Get the response
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': 500,
            'body': 'Error calling NREL API'
        }
    else:
        data = response.json()

    hsp = data['outputs']['solrad_annual']
    ac_monthly = data['outputs']['ac_monthly']


    # Create the production image
    prod_img = os.path.join(config.TEMP_DIR, 'monthly_production.png')
    createProductionImage(ac_monthly, prod_img)

    # Calculate the anual production and consumption
    anual_production =  math.floor(sum(ac_monthly))
    yearlyKWhEnergyConsumption = math.ceil(avg_daily_consumption * 365)

    # percentage of annual saves
    savings_percentage = round(anual_production / yearlyKWhEnergyConsumption * 100, 1)
    n_panels = int(system_capacity//(panels_capacity/1000))
    req_area = math.ceil(n_panels * config.PANELS_AREA[panels_capacity])
    avgCostPerKw = config.AVG_INSTALLED_COST_PER_KW

    # Financials
    # Calculate the cost of the system
    installationCost = localInstalationCostModel(system_capacity, avgCostPerKw)

    billWithSolar = lifetimeUtilityBillwithSolar(
        yearlyKWhEnergyConsumption=yearlyKWhEnergyConsumption,
        initialAcKwhPerYear=anual_production,
        efficiencyDepreciationFactor=1,
        installationLifeSpan=config.INSTALLATION_LIFE_SPAN,
        costIncreaseFactor=config.COST_INCREASE_FACTOR,
        discountRate=config.DISCOUNT_RATE,
        costPerKwh=costPerKwh)
    
    billWithoutSolar = lifetimeUtilityBillwithoutSolar(
        yearlyKWhEnergyConsumption=yearlyKWhEnergyConsumption,
        costIncreaseFactor=config.COST_INCREASE_FACTOR,
        discountRate=config.DISCOUNT_RATE,
        installationLifeSpan=config.INSTALLATION_LIFE_SPAN,
        costPerKwh=costPerKwh)
    
    totalCostWithSolar = installationCost + sum(billWithSolar) - config.INCENTIVES
    costOfElectricityWithoutSolar = sum(billWithoutSolar)

    savings = costOfElectricityWithoutSolar - totalCostWithSolar

    savingsFirstYear = billWithoutSolar[0] - billWithSolar[0]

    # Create the utility bill chart
    utility_bill_img = os.path.join(config.TEMP_DIR, 'utility_bill_chart.png')
    createUtilityBillChart(installationCost, billWithSolar, billWithoutSolar, utility_bill_img)

    # Fill the word template
    # Define paths and context
    template_path = 'wattsonReportTemplate.docx'
    output_path = os.path.join(config.TEMP_DIR, 'prodReport.docx')
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
        'consumoAnual': yearlyKWhEnergyConsumption,
        'PorcAhorroAnual': savings_percentage,
        'areaRequerida': req_area,
        'tiempoVidaPy': config.INSTALLATION_LIFE_SPAN,
        'ahorroMensual': formatNumberToCurrency(savingsFirstYear/12),
        'ahorroAnual': formatNumberToCurrency(savingsFirstYear),
        'costoInstalacion': formatNumberToCurrency(installationCost),
        'CostoSinPaneles': formatNumberToCurrency(costOfElectricityWithoutSolar),
        'CostoConPaneles': formatNumberToCurrency(totalCostWithSolar),
        'ahorroTotal': formatNumberToCurrency(savings),
    }

    img_context = {
        'imglUbicacion': {'path': location_img, 'width': 45},
        'imglProduccion': {'path': prod_img, 'width': 130},
        'imglFlujoCostos': {'path': utility_bill_img, 'width': 130}
    }

    fill_word_template(template_path, output_path, template_context, img_context)

    # Save report to S3
    logger.info(f"Saving report to S3")
    bucket = os.environ['UploadBucket']
    try:                            
        docx_key = getReportKey(userId, conversationId, 'docx')
        docx_url = saveDocxInS3(open(output_path, 'rb'), bucket, docx_key)
        docx_signed_url = getGetterSignedUrl(bucket, docx_key)
    except Exception as e:
        logger.error(f"Error saving report to S3: {e}")
        return {
            'statusCode': 500,
            'body': 'Error saving report to S3'
        }

    # Convert the docx to pdf
    logger.info(f"Converting docx to pdf")
    filename = docx_key.split('/')[-1]
    pdf_filename = f"Informe Solar {filename}".replace('.docx', '.pdf')
    pdf_key = docx_key.replace(filename, pdf_filename)

    try:
        pdf_signed_url = getUploaderSignedUrl(bucket, pdf_key)
        conversion_ok = convert_docx_to_pdf_with_api2pdf(config.API2PDF_API_KEY, docx_signed_url, pdf_signed_url, pdf_filename)
        changeMetadata(bucket, pdf_key)
        output_url = getGetterSignedUrl(bucket, pdf_key)
    except Exception as e:
        logger.error(f"Error converting docx to pdf: {e}")
        return {
            'statusCode': 500,
            'body': 'Error converting docx to pdf'
        }

    # Return the signed url
    return {
        'statusCode': 200,
        'body': json.dumps({'pdfUrl': output_url})
    }
