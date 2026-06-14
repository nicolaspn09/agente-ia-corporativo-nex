import pandas as pd
import re

# Load the CSV files
try:
    df_contatos = pd.read_csv(r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\contacts.csv")
    df_contacts = pd.read_csv(r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\contatos.csv")
except FileNotFoundError as e:
    print(f"Erro: Arquivo não encontrado. Certifique-se de que 'contatos.csv' e 'contacts.csv' foram carregados corretamente. Detalhes: {e}")
    # Exit or handle the error appropriately
    exit()


# Concatenate the two dataframes
df_combined = pd.concat([df_contatos, df_contacts], ignore_index=True)

extracted_contacts = []

# Define a list of phone columns to iterate through
phone_columns = ['Phone 1', 'Phone 2', 'Phone 3', 'Phone 4', 'Phone 5', 'Phone 6']

for index, row in df_combined.iterrows():
    # Construct full name
    first_name = str(row['First Name']) if pd.notna(row['First Name']) else ''
    middle_name = str(row['Middle Name']) if pd.notna(row['Middle Name']) else ''
    last_name = str(row['Last Name']) if pd.notna(row['Last Name']) else ''

    full_name_parts = [first_name, middle_name, last_name]
    full_name = ' '.join(filter(None, full_name_parts)).strip()

    # Iterate through phone columns
    for col_prefix in phone_columns:
        label_col = f'{col_prefix} - Label'
        value_col = f'{col_prefix} - Value'

        # Check if the columns exist in the current row's dataframe (important for concat which might have NaNs for missing cols)
        if label_col in row.index and value_col in row.index:
            phone_label = str(row[label_col]).lower() if pd.notna(row[label_col]) else ''
            phone_value = str(row[value_col]) if pd.notna(row[value_col]) else ''

            # Check if it's a mobile number and not a fixed line
            # This regex checks for a few mobile-related terms like 'mobile', 'celular', 'versão antiga'
            # and excludes common fixed line terms like 'fixo', 'comercial', 'principal', 'home'
            # Also, added 'main' as a mobile indicator as seen in some samples (Phone 1 - Label: * Work / Main)
            if re.search(r'\b(mobile|celular|versão antiga|work|main)\b', phone_label) and not re.search(r'\b(fixo|comercial|principal|home)\b', phone_label):

                # Clean the phone number
                cleaned_number = re.sub(r'\D', '', phone_value)  # Remove all non-digits

                # Remove '021' if present at the beginning, only if it's followed by DDD + number
                # A Brazilian mobile number (after country code) is 2-digit DDD + 9-digit number
                # So total should be 11 digits after 55. If 021 is present, it will be 3 + 11 = 14 digits.
                if cleaned_number.startswith('021') and len(cleaned_number) >= 12: # 021 + DDD (2) + NNNNNNNN (8 or 9)
                    cleaned_number = cleaned_number[3:]

                # Add '55' prefix if not already present
                if not cleaned_number.startswith('55'):
                    cleaned_number = '55' + cleaned_number

                # Only consider numbers that look like valid Brazilian mobile numbers (55 + 2-digit DDD + 8 or 9 digits)
                # This makes the total length 12 or 13 digits (55 + 2 + 8/9)
                if re.match(r'^55\d{10,11}$', cleaned_number):
                    extracted_contacts.append({'Name': full_name, 'Number': cleaned_number})

# Create a DataFrame from the extracted contacts
df_extracted = pd.DataFrame(extracted_contacts)

# Remove duplicates based on 'Name' and 'Number'
df_extracted.drop_duplicates(inplace=True)

# Format the output as 'Nome completo | número'
df_extracted['Formatted Contact'] = df_extracted['Name'] + ' | ' + df_extracted['Number']

# Prepare the content to be written to the file
file_content = "Formatted Contact\n" + df_extracted['Formatted Contact'].str.cat(sep='\n')

# Print the content directly for the user to copy
print(file_content)