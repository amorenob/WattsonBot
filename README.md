# WattsonBot

WattsonBot is a Botpress implementation designed to assist in the estimation and implementation of off-grid solar systems in Colombia. This bot is created to guide users through the process of evaluating their energy needs and providing an estimate of the appropriate solar system size and cost.

For a live demo of this Bot got to: https://mediafiles.botpress.cloud/a12b9dbb-13e2-492a-89b7-26a7358d0d79/webchat/bot.html

# System Architecture

## BotpressBot
Handles user interactions, guiding them through the process of providing necessary information for solar system estimation. It collects data such as average monthly energy consumption, last month's consumption, and the cost of the last energy bill.

## AWS Serverless Backend / API
Processes the information provided by the user to calculate the most suitable solar system size. It also generates a detailed production report, including a cost analysis and estimated energy production.

## External APIs
WattsonBot integrates with several external APIs:

* Google Maps Geocoding API: Used to obtain the coordinates of the user's location based on their address.
* PVWATTS API: Provided by the National Renewable Energy Laboratory (NREL), this API is used to estimate the solar potential and energy production of the proposed solar system. It considers factors such as location, system size, and panel orientation to provide precise energy production estimates.
* API2PDF: Converts the production report, which includes detailed production and cost analysis, into a PDF format. 

Important: this application uses various AWS services and there are costs associated with these services after the Free Tier usage - please see the [AWS  pricing page](https://aws.amazon.com/pricing/) for details.


## Requirements

* AWS CLI already configured with Administrator permission
* SAM CLI. You can follow the [official guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) for installation instructions.
* [NodeJS 16.x installed](https://nodejs.org/en/download/)
* Python 3.1x
* [Google Maps Geocoding API Key](https://developers.google.com/maps/documentation/geocoding/get-api-key)
* [PVWatts API Key](https://developer.nrel.gov/docs/solar/pvwatts/v8/)
* [API2PDF API Key](https://portal.api2pdf.com/register)

## Installation Instructions

Clone this repository:

```bash

git clone https://github.com/amorenob/WattsonBot.git

```


# Botpress bot
1. [Create an Botpress account](https://botpress.com/) if you do not already have one and login.
2. [Import the WattsonBot template](https://botpress.com/docs/cloud/studio/import-export/) 
3. Go to the bot settings an configure the env variables `PVWATTS_API_KEY` and `GOOGLE_API_KEY`
![alt text](image.png)


# Backend API
1. [Create an AWS account](https://portal.aws.amazon.com/gp/aws/developer/registration/index.html) if you do not already have one and login.
2. Build and deploy. 
Navigate to the root directory of the application and run the following commands:
```bash

sam build
sam deploy --guided
```
The `sam build` command will build the source of your application. The `sam deploy --guided` command will package and deploy your application to AWS, guided by prompts for configuration parameters.
This will create and deploy the serverless project with AWS Lambda functions. T





# How to edit the Production Report



# Serverless BackEnd

## GetProdReport Function

The `GetProdReport` function is responsible for generating an estimated production report for solar energy projects.

The function is implemented as an AWS Lambda function, which is triggered via an HTTP GET request. The function uses various parameters such as the location, system capacity, and average daily consumption to call the NREL API and retrieve solar radiation data.

The function then processes this data to calculate the annual solar energy production, the number of solar panels required, and the required area for the solar panels. It also calculates the financial aspects of the project, such as the installation cost, the utility bill with and without solar, and the total cost with solar after incentives.

The function generates a production image showing the monthly production of solar energy and saves it along with the report data in an Amazon S3 bucket.

To use the `GetProdReport` function, you need to send a GET request to the `/prod-report` endpoint with the required parameters. The function will then generate the report and return a signed URL to access the report in the S3 bucket.

Please note that this function requires certain environment variables to be set, such as the NREL API key, Google API key, and API2PDF API key. These keys are used to call the respective APIs for data retrieval and report generation.









## Using this Application

* This application creates an API Gateway endpoint where your application can request a pre-signed URL to upload JPG objects to an S3 bucket. Once the API returns the URL, your application can PUT the object data to this URL to complete the upload.


## How it works

* Deploy this serverless application and take a note of the API endpoint.
* Invoke the API to receive a pre-signed URL for uploading a JPG file. Use this pre-signed URL to complete the upload.
* For a live example of this, see [this Fiddle](https://jsfiddle.net/jbeswick/Lq3vkdx2/). View the browser console to see logs of how the Fiddle is interacting with the API Gateway and presigned URL.

==============================================
