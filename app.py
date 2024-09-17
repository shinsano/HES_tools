from flask import Flask, request, render_template, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = '26calvert'

# Define the mapping globally or within a function
subtype_mapping = {
    'Gas Furnace': {
        'The furnace has white PVC pipe exhaust venting (Condensing).': 'Condensing',
        'It has an inducer fan unit (Induced Draft).': 'Induced Draft',
        'It has a draft hood or opening that enters directly into the flue, with heat exchanger and gas burner ports behind louvered cover panel (Natural Draft).': 'Natural Draft',
    },
    'Gas Boiler': {
        'Condensing': 'Condensing',
        'Induced Draft': 'Induced Draft',
        'Natural Draft': 'Natural Draft',
    },
    'Gas Local Equipment': {
        'Room (through-the-wall) gas furnace': 'Room (through-the-wall) gas furnace',
    },
    'Oil Furnace': {
        'The furnace has white PVC pipe sealed exhaust venting (Condensing).': 'Condensing',
        'It has motor RPM 3450, standard since mid-1980\'s, with natural draft exhaust venting with barometric damper on metal flue (Flame-Retention Head).': 'Flame-Retention Head',
        'It has motor RPM 1725, phased out in 1980\'s, with natural draft exhaust venting with barometric damper on metal flue (Conventional).': 'Conventional',
    },
    'Oil Boiler': {
        'Induced Draft': 'Induced Draft',
        'Natural Draft': 'Natural Draft',
    },
    'Electric Furnace': {
        'Electric Furnace': 'Electric Furnace',
    },
    'Electric Boiler': {
        'Electric Boiler': 'Electric Boiler',
    },
    'Electric Heat Pump': {
        'It has a large outside unit (Electric Air Source Heat Pump).': 'Electric Air Source Heat Pump',
        'It has a thin profile outside unit (Minisplit (Ductless) Heat Pump).': 'Minisplit (Ductless) Heat Pump',
    },
    'Electric Local Equipment': {
        'Electric Baseboard Heater': 'Electric Baseboard Heater',
    },
    'Geothermal Heat Pump': {
        'Geothermal Heat Pump (Ground Coupled)': 'Ground Coupled Heat Pump',
    },
    'Wood/coal Local Equipment': {
        'Wood Stove': 'Wood Stove',
        'Pellet Stove': 'Pellet Stove',
    },
}


@app.route('/')
def home():
    # Clear the session data
    session.clear()
    return render_template('home.html')



@app.route('/fuel', methods=['GET', 'POST'])
def fuel():
    if request.method == 'POST':
        session['fuel'] = request.form.get('fuel_type')
        return redirect(url_for('identify_equipment'))
    return render_template('fuel.html', fuel_types=['Gas', 'Oil', 'Electric', 'Wood/coal', 'Geothermal'])


@app.route('/identify_equipment', methods=['GET', 'POST'])
def identify_equipment():
    if request.method == 'POST':
        session['equipment'] = request.form.get('equipment_type')
        return redirect(url_for('identify_subtype'))
    
    fuel = session.get('fuel', None)
    equipment_options = {
        'Gas': ['Furnace', 'Boiler', 'Local Equipment'],
        'Oil': ['Furnace', 'Boiler'],
        'Electric': ['Furnace', 'Boiler', 'Heat Pump', 'Local Equipment'],
        'Geothermal': ['Heat Pump'],
        'Wood/coal': ['Local Equipment']
    }
    equipments = equipment_options.get(fuel, [])
    return render_template('identify_equipment.html', equipments=equipments)

@app.route('/identify_subtype', methods=['GET', 'POST'])
def identify_subtype():
    if request.method == 'POST':
        selected_description = request.form.get('equipment_subtype')
        fuel = session.get('fuel')
        equipment = session.get('equipment')
        key = f"{fuel} {equipment}"

        # Use the mapping to get the actual subtype
        subtype = subtype_mapping.get(key, {}).get(selected_description)
        
        if subtype:
            # Standardize the subtype value
            subtype = subtype.strip().title()
            # Store the standardized subtype in the session
            session['subtype'] = subtype
            return redirect(url_for('collect_details'))
        else:
            # Handle the case where subtype is not found
            flash("Invalid selection. Please try again.")
            return redirect(url_for('identify_subtype'))

    # For GET request, render the template with subtype options
    fuel = session.get('fuel')
    equipment = session.get('equipment')
    subtypes = get_equipment_subtype_options(fuel, equipment)
    return render_template('identify_subtype.html', subtypes=subtypes, fuel=fuel, equipment=equipment)


# Helper function
def get_equipment_subtype_options(fuel, equipment):
    options = subtype_mapping.get(f"{fuel} {equipment}", {})
    return list(options.keys())

    

@app.route('/collect_details', methods=['GET', 'POST'])
def collect_details():
    if request.method == 'POST':
        year = request.form.get('year')
        energy_star = request.form.get('energy_star', 'no').lower()

        # Only get 'state' if it's included in the form
        state = request.form.get('state')
        if state:
            state = state.upper()
            session['state'] = state
        else:
            session['state'] = None  # Handle cases where 'state' is not provided

        session['year'] = year
        session['energy_star'] = energy_star

        return redirect(url_for('show_result'))

    # Determine whether to collect 'state'
    fuel = session.get('fuel')
    equipment = session.get('equipment')
    collect_year_energy_star = fuel in ['Gas', 'Oil'] or (fuel == 'Electric' and equipment == 'Heat Pump')
    collect_state = fuel == 'Gas' and equipment == 'Furnace'

    return render_template(
        'collect_details.html',
        collect_year_energy_star=collect_year_energy_star,
        collect_state=collect_state
    )




@app.route('/show_result', methods=['GET', 'POST'])
def show_result():
    # Retrieve session variables
    fuel = session.get('fuel')
    equipment = session.get('equipment')  # Add this line
    subtype = session.get('subtype')
    year = session.get('year')
    energy_star = session.get('energy_star')
    state = session.get('state')

    # Process ENERGY STAR status
    if energy_star == 'yes':
        energy_star_status = 'ENERGY STAR'
    else:
        energy_star_status = 'not ENERGY STAR'

    # Calculate efficiency
    efficiency_info = get_efficiency(fuel, equipment, subtype, year, energy_star, state)

    # Build equipment details dictionary
    equipment_details = {
        'Fuel': fuel,
        'Equipment': equipment,
        'Subtype': subtype,
        'Year': year,
        'ENERGY STAR Status': energy_star_status,
        'Efficiency': efficiency_info.get('efficiency', 'N/A'),
        'State': state,
    }

    # Store equipment_details in session
    if 'equipment_list' not in session:
        session['equipment_list'] = []
    equipment_list = session['equipment_list']
    equipment_list.append(equipment_details)
    session['equipment_list'] = equipment_list

    return render_template('result.html', equipment_details=equipment_details)


@app.route('/another_equipment', methods=['POST'])
def another_equipment():
    another = request.form.get('another')
    if another == 'yes':
        # Redirect to the beginning of the identification process
        return redirect(url_for('fuel'))
    else:
        # Redirect to the summary page
        return redirect(url_for('summary'))
    
@app.route('/summary')
def summary():
    equipment_list = session.get('equipment_list', [])
    return render_template('summary.html', equipment_list=equipment_list)

    

def get_state():
    # List of US states and abbreviations
    states = {
        'AK': 'Alaska', 'AL': 'Alabama', 'AR': 'Arkansas', 'AZ': 'Arizona', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
        'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'MA': 'Massachusetts', 'MD': 'Maryland',
        'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota', 'MO': 'Missouri', 'MS': 'Mississippi',
        'MT': 'Montana', 'NC': 'North Carolina', 'ND': 'North Dakota', 'NE': 'Nebraska',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NV': 'Nevada',
        'NY': 'New York', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
        'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
        'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia', 'VT': 'Vermont', 'WA': 'Washington',
        'WI': 'Wisconsin', 'WV': 'West Virginia', 'WY': 'Wyoming', 'DC': 'District of Columbia'
    }
    while True:
        state_input = input("Enter the state abbreviation (e.g. CA for California): ")
        if state_input in states:
            region = determine_region(state_input)
            return states[state_input], region
        else:
            print("Invalid state abbreviation. Please try again.")

def determine_region(state):
    north_states = [
        'AK', 'CO', 'CT', 'ID', 'IL', 'IN', 'IA', 'KS', 'ME', 'MA', 'MI', 'MN', 'MO', 'NE', 'NH',
        'NJ', 'NY', 'ND', 'OH', 'OR', 'PA', 'RI', 'SD', 'UT', 'VT', 'WA', 'WV', 'WI', 'WY'
    ]
    south_states = [
        'AL', 'AZ', 'AR', 'CA', 'DE', 'DC', 'FL', 'GA', 'HI', 'KY', 'LA', 'MD', 'MS', 'NV',
        'NM', 'NC', 'OK', 'SC', 'TN', 'TX', 'VA'
    ]
    if state in north_states:
        return 'North'
    elif state in south_states:
        return 'South'
    else:
        print("State not found in region lists. Defaulting to South.")
        return 'South'
    
def get_heat_pump_efficiency(subtype, year, energy_star):
    # Check if the subtype is Minisplit
    if subtype == 'Minisplit (Ductless) Heat Pump':
        return '10.0'
    else:
        # Existing logic for other subtypes
        if energy_star == 'yes':
            if year >= 2015:
                return '8.5'
            elif 2006 <= year <= 2015:
                return '8.2'
            else:
                return '8.2'  # Default ENERGY STAR prior to 2015
        else:
            if year >= 2015:
                return '8.2'
            elif 2006 <= year <= 2014:
                return '7.7'
            elif 1992 <= year <= 2005:
                return '7.1'
            else:
                return '6.6'



def get_gas_furnace_efficiency(subtype, year, energy_star, region):
    print(f"Calculating efficiency for subtype: {subtype}, year: {year}, energy_star: {energy_star}, region: {region}")
    # Convert year to int
    if year:
        year = int(year)

    if energy_star == 'yes':
        if year >= 2015:
            if region == 'North':
                return '0.95'
            else:
                return '0.90'
        else:
            return '0.90'  # ENERGY STAR prior to 2015
    else:
        if subtype == 'Condensing':
            return '0.90'
        elif subtype == 'Induced Draft':
            return '0.82'
        elif subtype == 'Natural Draft':
            return '0.78'
        else:
            return 'Unknown AFUE'

def get_gas_boiler_efficiency(subtype, year, energy_star):
    # Convert year to int
    if not isinstance(year, int):
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = 0  # Assign a default value or handle the error

    if energy_star == 'yes':
        if year >= 2014:
            return '0.90'
        elif 2004 <= year < 2014:
            return '0.85'
        else:
            return '0.85'  # Default ENERGY STAR prior to 2004
    else:
        if subtype == 'Condensing':
            return '0.90'
        elif subtype == 'Induced Draft':
            return '0.82'
        elif subtype == 'Natural Draft':
            return '0.78'
        else:
            return 'Unknown AFUE'
        
def get_oil_furnace_efficiency(subtype, year, energy_star):
    # Convert year to int
    if not isinstance(year, int):
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = 0  # Assign a default value or handle the error

    if subtype == 'Condensing':
        return '0.90'
    elif energy_star == 'yes':
        if year >= 2003:
            return '0.85'
        else:
            return '0.85'  # Default ENERGY STAR prior to 2003
    else:
        if subtype == 'Flame-Retention Head':
            return '0.80'
        elif subtype == 'Conventional':
            return '0.72'
        else:
            return 'Unknown AFUE'

def get_oil_boiler_efficiency(subtype, year, energy_star):
    # Convert year to int
    if not isinstance(year, int):
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = 0  # Assign a default value or handle the error

    if energy_star == 'yes':
        if year >= 2014:
            return '0.87'
        elif 2002 <= year < 2014:
            return '0.85'
        else:
            return '0.85'  # Default ENERGY STAR prior to 2002
    else:
        if subtype == 'Induced Draft':
            return '0.82'
        elif subtype == 'Natural Draft':
            return '0.78'
        else:
            return 'Unknown AFUE'
        
def get_efficiency(fuel, equipment, subtype, year=None, energy_star=None, state=None):
    efficiency_info = {}
    # Convert year to int
    if year is not None:
        year = int(year)
    
    # Collect additional details based on conditions
    if fuel in ['Gas', 'Oil'] or (fuel == 'Electric' and equipment == 'Heat Pump'):
        efficiency_info['year'] = year
        efficiency_info['energy_star'] = energy_star

    if fuel == 'Gas' and equipment == 'Furnace':
        if state:
            efficiency_info['state'] = state
            region = determine_region(state)
        else:
            # Handle the case where 'state' is None
            region = 'South'  # Default region or handle as appropriate
        afue = get_gas_furnace_efficiency(subtype, year, energy_star, region)
        efficiency_info['efficiency'] = f"AFUE {afue}"

    elif fuel == 'Electric' and equipment == 'Furnace':
        efficiency_info['efficiency'] = 'AFUE 0.99'
    elif fuel == 'Electric' and equipment == 'Boiler':
        efficiency_info['efficiency'] = 'AFUE 0.97'
    elif fuel == 'Electric' and equipment == 'Local Equipment':
        efficiency_info['efficiency'] = 'AFUE 0.99'
    elif fuel == 'Electric' and equipment == 'Heat Pump':
        efficiency_info['efficiency'] = get_heat_pump_efficiency(subtype, year, energy_star)
    elif fuel == 'Geothermal' and equipment == 'Heat Pump':
        efficiency_info['efficiency'] = 'Efficiency data not provided'
    elif fuel == 'Gas' and equipment == 'Boiler':
        efficiency_info['efficiency'] = get_gas_boiler_efficiency(subtype, year, energy_star)
    elif fuel == 'Oil' and equipment == 'Furnace':
        efficiency_info['efficiency'] = get_oil_furnace_efficiency(subtype, year, energy_star)
    elif fuel == 'Oil' and equipment == 'Boiler':
        efficiency_info['efficiency'] = get_oil_boiler_efficiency(subtype, year, energy_star)
    else:
        efficiency_info['efficiency'] = 'Efficiency data not available'

    return efficiency_info


if __name__ == "__main__":
    app.run(debug=True)
