import pandas as pd
from datetime import datetime, timedelta

# Updated file paths
export_file_path = r'FILE_PATH_HERE'  # Input file path
updated_output_file_path = r'FILE_PATH_HERE'  # Output file path

# Load the export file
export_df = pd.read_csv(export_file_path)

# Helper functions for calculations and formatting
def format_address(address_column):
    """Formats address by removing town and postal code and keeping house and street names."""
    def exclude_town(address):
        if pd.notna(address):
            parts = address.split(",")
            if len(parts) > 2:
                return ", ".join([p.strip() for p in parts[:-2]])  # Keep house and street names
            return address.strip()
        return None
    return address_column.apply(lambda x: f"[{exclude_town(x)}]" if pd.notna(x) else None)

def extract_service_type(name):
    """Determines the service type based on the product name."""
    if pd.notna(name):
        if any(product in name for product in ["Fresh 150", "Fresh 500", "Fresh 900"]):
            return "IAS"
        elif "Fresh Talk" in name:
            return "NBICS"
    return None

def reformat_product_name(name):
    """Simplifies product names to the first two words."""
    if pd.notna(name):
        words = name.split()
        return " ".join(words[:2])
    return None

def calculate_end_date(activation_date):
    """Calculates the end date, 18 months from the activation date."""
    try:
        start_date = pd.to_datetime(activation_date)
        end_date = start_date + pd.DateOffset(months=18)
        return end_date.strftime("%d/%m/%y")
    except (ValueError, TypeError):
        return None

def calculate_remaining_months(end_date):
    """Calculates remaining months until the end date."""
    try:
        end_date_obj = pd.to_datetime(end_date, format="%d/%m/%y")
        remaining_days = (end_date_obj - datetime.now()).days
        return max(remaining_days // 30, 0)
    except (ValueError, TypeError):
        return None

def map_product_to_custom6(name):
    """Maps product names to corresponding Custom6 values."""
    mapping = {
        "Fresh 150": 18,
        "Fresh 500": 20.4,
        "Fresh 900": 22.8,
        "Fresh Talk": 17
    }
    return mapping.get(name, None)

def calculate_custom7(custom5, custom6, registration_date):
    """Calculates Custom7 value based on remaining months and registration date."""
    try:
        reg_date = pd.to_datetime(registration_date)
        if custom5 == 0 or reg_date >= datetime.now() - timedelta(days=14):
            return 60
        elif custom5 and custom6:
            return custom5 * custom6 + 120
    except (ValueError, TypeError):
        pass
    return None

# Preprocessing and intermediate calculations
export_df['Calculated_End_Date'] = export_df['activation_date'].apply(calculate_end_date)
export_df['Remaining_Months'] = export_df['Calculated_End_Date'].apply(calculate_remaining_months)
export_df['Custom2_Reformatted'] = export_df['name'].apply(reformat_product_name)
export_df['Custom6_Value'] = export_df['Custom2_Reformatted'].apply(map_product_to_custom6)
export_df['Custom7_Debug'] = export_df.apply(
    lambda row: calculate_custom7(row['Remaining_Months'], row['Custom6_Value'], row['registration_date']),
    axis=1
)

# Reformat export data based on the template mapping
reformatted_data = pd.DataFrame({
    "RCPID": "RWLC",
    "LRCPBrandName": "Fresh Fibre",
    "Uprn": export_df.get("uprn"),
    "AddressPAFAddressLines": format_address(export_df.get("address")),
    "AddressPostTown": export_df.get("town"),
    "AddressPostcode": export_df.get("postcode"),
    "ServiceType": export_df.get("name").apply(extract_service_type),
    "ServiceIdentifierType": export_df.get("name").apply(extract_service_type),
    "ServiceIdentifier": export_df.get("name").apply(extract_service_type),
    "Account": export_df.get("code"),
    "Name": export_df.get("contact_surname"),
    "PostalAddressPAFAddressLines": format_address(export_df.get("address")),
    "PostalAddressPostTown": export_df.get("town"),
    "PostalAddressPostcode": export_df.get("postcode"),
    "Email": export_df.get("email"),
    "MobileNumber": export_df.get("phone"),
    "CommunicationPreferenceId": 1,
    "Custom1": export_df.get("contact_name"),
    "Custom2": export_df['Custom2_Reformatted'],
    "Custom3": export_df.get("registration_date"),
    "Custom4": export_df['activation_date'].apply(lambda x: x.split()[0] if pd.notna(x) else None),
    "Custom5": export_df['Remaining_Months'],
    "Custom6": export_df['Custom6_Value'],
    "Custom7": export_df['Custom7_Debug'],
    "Custom8": "Zyxel Router",
    "Custom9": "PHONE_NUMBER",
    "Custom10": "EMAIL"
})

# Save the updated data to the specified local file
reformatted_data.to_csv(updated_output_file_path, index=False, encoding='utf-8', header=True)

print(f"Reformatted data saved to: {updated_output_file_path}")
