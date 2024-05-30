import requests
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import datetime
import config

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

def getLocationImage(lat, lon, google_api_key):
    """
    Retrieves a static map image for a given location using the Google Maps API.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        google_api_key (str): API key for accessing the Google Maps API.

    Returns:
        requests.Response: The response object containing the static map image.

    Raises:
        requests.exceptions.RequestException: If an error occurs while making the API request.
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}"
        url += "&zoom=14"
        url += "&size=310x310"
        url += "&maptype=roadmap"
        url += f"&markers=color:red%7C{lat},{lon}"
        url += f"&key={google_api_key}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-successful status codes
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def getLocationInfo(lat, lon, google_api_key):
    """
    Retrieves location information based on latitude and longitude using the Google Geocoding API.

    Args:
        lat (float): The latitude of the location.
        lon (float): The longitude of the location.
        google_api_key (str): The API key for accessing the Google Geocoding API.

    Returns:
        requests.Response or None: The response object containing the location information if successful,
        None if an error occurred.
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={google_api_key}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-successful status codes
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def calculateOptimalTilt(lat):
    """
    Calculate the optimal tilt for a solar panel based on the latitude.

    Parameters:
    lat (float): The latitude in degrees.

    Returns:
    float: The optimal tilt angle in degrees.
    """
    lat = float(lat)
    # Calculate the optimal tilt
    tilt = lat - 2.5
    return round(tilt, 2)

def getProduction(api_key, lat, lon, system_capacity, azimut=180, tilt=0, losses=14, array_type=1, module_type=1):
    """
    Retrieves the solar production data using the PVWatts API.

    Args:
        api_key (str): The API key for accessing the PVWatts API.
        lat (float): The latitude of the location.
        lon (float): The longitude of the location.
        system_capacity (float): The capacity of the solar system in kilowatts (kW).
        azimut (float, optional): The azimuth angle of the solar panels in degrees. Defaults to 180.
        tilt (float, optional): The tilt angle of the solar panels in degrees. Defaults to 0.
        losses (float, optional): The system losses in percentage. Defaults to 14.
        array_type (int, optional): The array type. Defaults to 1.
        module_type (int, optional): The module type. Defaults to 1.

    Returns:
        dict: The solar production data in JSON format.

    Raises:
        requests.exceptions.RequestException: If an error occurs while making the API request.
    """
    try:
        url = f"https://developer.nrel.gov/api/pvwatts/v6.json?api_key={api_key}&lat={lat}&lon={lon}&system_capacity={system_capacity}"
        url += f"&azimuth={azimut}"
        url += f"&tilt={tilt}"
        url += f"&array_type={array_type}"
        url += f"&module_type={module_type}"
        url += f"&losses={losses}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-successful status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def createProductionImage(ac_monthly, output_path):
    # Create a figure and a set of subplots

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
    plt.tight_layout()  # Adjust the layout to prevent legend cutoff
    plt.savefig(output_path)


### solar financials

def lifetimeProductionAcKwh(
    dcToAcDerate,
    yearlyEnergyDcKwh,
    efficiencyDepreciationFactor,
    installationLifeSpan):
    """
    Calculate the lifetime production of AC energy in kilowatt-hours (kWh) for a solar installation.

    Args:
        dcToAcDerate (float): The DC to AC derate factor.
        yearlyEnergyDcKwh (float): The yearly energy production in DC kilowatt-hours (kWh).
        efficiencyDepreciationFactor (float): The efficiency depreciation factor.
        installationLifeSpan (int): The expected lifespan of the installation in years.

    Returns:
        float: The lifetime production of AC energy in kilowatt-hours (kWh).
    """
    return (
        dcToAcDerate *
        yearlyEnergyDcKwh *
        (1 - pow(
            efficiencyDepreciationFactor,
            installationLifeSpan)) /
        (1 - efficiencyDepreciationFactor))

def billCostModel(
    energy,
    costPerKwh):
  return energy * costPerKwh

def annualProduction(
    initialAcKwhPerYear,
    efficiencyDepreciationFactor,
    year):
    """
    Calculate the annual production of a solar panel system.

    Parameters:
    - initialAcKwhPerYear (float): The initial AC kWh production per year.
    - efficiencyDepreciationFactor (float): The efficiency depreciation factor.
    - year (int): The number of years since the installation.

    Returns:
    - float: The annual production of the solar panel system.

    """
    return initialAcKwhPerYear * pow(efficiencyDepreciationFactor, year)


def annualUtilityBillEstimate(
    yearlyKWhEnergyConsumption,
    initialAcKwhPerYear,
    efficiencyDepreciationFactor,
    year,
    costIncreaseFactor,
    discountRate,
    costPerKwh):
    """
    Calculates the estimated annual utility bill based on the given parameters.

    Parameters:
    - yearlyKWhEnergyConsumption: The total yearly energy consumption in kilowatt-hours.
    - initialAcKwhPerYear: The initial AC energy production in kilowatt-hours per year.
    - efficiencyDepreciationFactor: The factor representing the efficiency depreciation over time.
    - year: The number of years since the initial AC energy production.
    - costIncreaseFactor: The factor representing the annual cost increase.
    - discountRate: The discount rate for future costs.
    - costPerKwh: The cost per kilowatt-hour.

    Returns:
    - The estimated annual utility bill.

    """
    return (
        billCostModel(
            yearlyKWhEnergyConsumption -
            annualProduction(
                initialAcKwhPerYear,
                efficiencyDepreciationFactor,
                year), costPerKwh) *
        pow(costIncreaseFactor, year) /
        pow(discountRate, year))

def lifetimeUtilityBillwithSolar(
    yearlyKWhEnergyConsumption,
    initialAcKwhPerYear,
    efficiencyDepreciationFactor,
    installationLifeSpan,
    costIncreaseFactor,
    discountRate,
    costPerKwh):
    """
    Calculate the lifetime utility bill with solar.

    Args:
        yearlyKWhEnergyConsumption (float): The yearly energy consumption in kWh.
        initialAcKwhPerYear (float): The initial AC kWh per year.
        efficiencyDepreciationFactor (float): The efficiency depreciation factor.
        installationLifeSpan (int): The lifespan of the installation in years.
        costIncreaseFactor (float): The cost increase factor.
        discountRate (float): The discount rate.
        costPerKwh (float): The cost per kWh.

    Returns:
        list: A list of utility bills for each year of the installation lifespan.
    """
    bill = [0] * installationLifeSpan
    for year in range(installationLifeSpan):
        bill[year] = annualUtilityBillEstimate(
            yearlyKWhEnergyConsumption,
            initialAcKwhPerYear,
            efficiencyDepreciationFactor,
            year,
            costIncreaseFactor,
            discountRate,
            costPerKwh)
    return bill

def lifetimeUtilityBillwithoutSolar(
    yearlyKWhEnergyConsumption,
    costIncreaseFactor,
    discountRate,
    installationLifeSpan,
    costPerKwh):
    """
    Calculate the lifetime utility bill without solar.

    Args:
        yearlyKWhEnergyConsumption (float): The yearly energy consumption in kilowatt-hours.
        costIncreaseFactor (float): The factor by which the cost increases each year.
        discountRate (float): The discount rate used for future cash flows.
        installationLifeSpan (int): The lifespan of the installation in years.
        costPerKwh (float): The cost per kilowatt-hour.

    Returns:
        list: A list of utility bills for each year of the installation lifespan.
    """
    bill = [0] * installationLifeSpan
    for year in range(installationLifeSpan):
        bill[year] = billCostModel(
            yearlyKWhEnergyConsumption,
            costPerKwh) * pow(costIncreaseFactor, year) / pow(discountRate, year)
    return bill


def localInstalationCostModel(installationSize, avgCostPerKw):
    """
    Calculate the local installation cost based on the installation size and average cost per kilowatt.

    Args:
        installationSize (float): The size of the installation in kilowatts.
        avgCostPerKw (float): The average cost per kilowatt.

    Returns:
        float: The total installation cost.

    """
    costPerkw = avgCostPerKw
    if installationSize > 20:
        costPerkw = avgCostPerKw - 17.5 * 130000
    elif installationSize > 2.5:
        costPerkw = avgCostPerKw - (installationSize - 2.5) * 130000

    return config.AVG_INSTALLATION_FIXED_COST + installationSize * costPerkw

def createUtilityBillChart(
        installationCost,
        billWithSolar,
        billWithoutSolar,
        output_path):
    billWithSolar[0] = +installationCost
    current_year = datetime.datetime.now().year
    years = range(current_year, current_year + len(billWithSolar))
    plt.figure(figsize=(10, 5))
    plt.plot(years, np.cumsum(billWithSolar) / 1000000, marker='o', label='Con paneles solares')
    plt.plot(years, np.cumsum(billWithoutSolar) / 1000000, marker='o', label='Sin paneles solares')
    plt.xlabel('Año')
    plt.ylabel('Costo acumulado ($COP, en millones)')
    plt.title('Costo acumulado de la factura eléctrica')
    # Tilt the month names on the x-axis
    plt.xticks(ticks=years, rotation=45, fontsize=8)  
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)  # Add horizontal grids
    plt.tight_layout()  # Adjust the layout to prevent legend cutoff
    plt.savefig(output_path)
    return output_path

if __name__ == "__main__":
    # Example usage of the functions
    yearlyKWhEnergyConsumption = 2300
    initialAcKwhPerYear = 1200
    efficiencyDepreciationFactor = 0.995
    installationLifeSpan = 25
    costIncreaseFactor = 1.05
    discountRate = 1.04
    installationCost = 8000000
    costPerKwh = 1300

    billWithSolar = lifetimeUtilityBillwithSolar(
        yearlyKWhEnergyConsumption,
        initialAcKwhPerYear,
        efficiencyDepreciationFactor,
        installationLifeSpan,
        costIncreaseFactor,
        discountRate,
        costPerKwh)
    billWithoutSolar = lifetimeUtilityBillwithoutSolar(
        yearlyKWhEnergyConsumption,
        costIncreaseFactor,
        discountRate,
        installationLifeSpan,
        costPerKwh)

    createUtilityBillChart(installationCost,billWithSolar, billWithoutSolar, "utility_bill_chart.png")

