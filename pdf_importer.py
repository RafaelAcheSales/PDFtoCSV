import PyPDF2
import os
import re
import csv
import sys

POSSIBLE_YEARS = ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
#REGEX  DICT POSITIONS (PRODUCT EXPRESSION, CNPJ EXPRESSION, DATE EXPRESSION)
RELATION_YEAR_REGEX = {
    '2012': (r"\b\d{7}\b\s(.*?)(?=\b\d{7}\b|\n|$)",),
    '2016': (r"\b\d{7}\b(.*?)-",),
    '2017': (r"\b\d{7}\b(.*?)-",),
    '2018': (r"\b\d{7}-F\b(.*?)-",),
    '2019': (r"\b\d{7}-F\b(.*?)-",),
    '2020': (r"\b\d{7}-F\b(.*?)-",),
    '2021': (r"\b\d{7}-F\b(.*?)-",),
    '2022': (r"\b\d{7}-F\b(.*?)-",),
}

class PDFTransformer:
    def __init__(self, filepath, year):
        self.filepath = filepath
        self.search_term = 'Valor Total: '
        self.output_file = 'tabela_produtos_output.csv'
        self.year = year

    def extract_products(self):
        count = 0
        with open(self.filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            all_products = []
            for page in pdf_reader.pages:
                current_text = page.extract_text()
                if current_text:
                    count += 1
                    # # print(f'Processing page {count}...')
                    print(current_text)
                    matching_products = self.extract_product_entries_from_page(current_text)
                    cnpj, date = self.extract_date_cnpj_from_page(current_text)
                    all_products.extend((cnpj, date, matching_products))

            return all_products

    def extract_product_entries_from_page(self, text):
        products = []
        pattern = RELATION_YEAR_REGEX[self.year][0]
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        for match in matches:
            print(match)
            product, values = self.extract_values_from_product(match)
            products.append((product, values))
        return products
        
    #example
    # RED HORSE DO BRASIL LTDACNPJ / CPF
    # 13.579.761/0001-91DATA DA EMISSÃO
    # 07/01/2013
    # ENDEREÇO

    #get value from CNPJ / CPF until DATA DA EMISSÃO then date next to it
    def extract_date_cnpj_from_page(self, text):
        # Regular expression for CNPJ/CPF (this is a basic pattern, may need to adjust)
        cnpj_pattern = r"CNPJ / CPF\s+([\d\.\/-]+)"
        cnpj_match = re.search(cnpj_pattern, text)
        cnpj = cnpj_match.group(1) if cnpj_match else None

        # Regular expression for the date
        date_pattern = r"DATA DA EMISSÃO\s+\n\s*(\d{2}/\d{2}/\d{4})"
        date_match = re.search(date_pattern, text)
        date = date_match.group(1) if date_match else None
        print(f'Found CNPJ {cnpj} Date: {date}')
        return cnpj, date


    #Example
    #  ENERGETICO RED HORSE ENERGY 22029000 6401 CX 493,00000 9,3000000 4.584,90 4.584,90 320,94 463,81 7.00% 0.00%12.116,90 1.738,93
    #  DRINK (PET) 2 L
    #  ENERGETICO RED HORSE (PET) 22029000 6401 CX 40,00000 8,4000000 336,00 336,00 23,52 23,52 7.00% 0.00% 862,85 123,17
    #  1 L
    #  ENERGETICO RED HORSE ENERGY 22029000 5401 CX 500,00000 9,3000000 4.650,00 4.650,00 790,50 470,40 17.00% 0.00%28.740,00 4.095,30
    #  DRINK (PET) 2 L
    def extract_values_from_product(self, product):
        # Split the product string at 'CX'
        parts = product.split('CX')
        
        # Check if the split was successful and there are at least two parts
        if len(parts) >= 2:
            # The first part is the product name, and the second part contains the values
            product_name = parts[0].strip()
            values_part = parts[1]

            # Extract the next three floats from the values part
            pattern = r"(\d+,\d+)\s+(\d+,\d+)\s+(\d+,\d+)"
            matches = re.search(pattern, values_part)
            if matches:
                return product_name, matches.groups()
            else:
                return product_name, None
        else:
            # If the split did not work as expected, return the whole product and None for values
            return product, None

def write_csv(products, output_file):
    for product in products:
        print(product)
        print(type(product))
    # HEADER = ['Produto', 'Quantidade', 'Valor Unitário', 'Valor Total']
    # with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    #     writer = csv.writer(csvfile, delimiter=',')
    #     writer.writerow(HEADER)
    #     for product in products:
    #         try:
    #             quantity = product[1][0]
    #             unit_value = product[1][1]
    #             total_value = product[1][2]
    #             writer.writerow([product[0], quantity, unit_value, total_value])
    #         except:
    #             pass


def process_pdfs(folder_path, year):
    total_products = []
    pdf_transformer = None
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, filename)
                pdf_transformer = PDFTransformer(pdf_path, year) 
                total_products.extend(pdf_transformer.extract_products())
    if not pdf_transformer:
        print(f'No PDF files found in {folder_path}.')
        return
    print(f'Found {len(total_products)} products in {folder_path}.')
    write_csv(total_products, pdf_transformer.output_file)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python pdf_importer.py <year>')
        sys.exit(1)
    year = sys.argv[1]
    if year not in POSSIBLE_YEARS:
        print('Invalid year')
        sys.exit(1)
    #path is pdfs\year
    path = os.path.join('pdfs', year)
    process_pdfs(path, year)
