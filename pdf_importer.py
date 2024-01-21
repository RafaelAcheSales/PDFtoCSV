import PyPDF2
import os
import re
import csv
import sys

POSSIBLE_YEARS = ['2008','2009','2010','2011',
                  '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
#REGEX  DICT POSITIONS (PRODUCT EXPRESSION, CNPJ EXPRESSION, DATE EXPRESSION)
RELATION_YEAR_REGEX = {
    '2008': (r"(\b\d{7}\b)(.*?)-|(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"), #2017
    '2009': (r"(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"),#2018
    '2010': (r"(\b\d{7}\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"), #2016
    '2011': (r"(\b\d{7}\b)\s([\s\S]*?)(?=\b\d{7}\b|$)",r"CNPJ / CPF\s+([\d\.\/-]+)", r"EMISSÃO:\s*(\d{2}/\d{2}/\d{4})", r"Nº\.\s*\d+(\.\d+)*"), #2012
    '2012': (r"(\b\d{7}\b)\s([\s\S]*?)(?=\b\d{7}\b|$)",r"CNPJ / CPF\s+([\d\.\/-]+)", r"EMISSÃO:\s*(\d{2}/\d{2}/\d{4})", r"Nº\.\s*\d+(\.\d+)*"),
    '2013': (r"(\b\d{7}\b)\s([\s\S]*?)(?=\b\d{7}\b|$)",r"CNPJ / CPF\s+([\d\.\/-]+)", r"EMISSÃO:\s*(\d{2}/\d{2}/\d{4})", r"Nº\.\s*\d+(\.\d+)*"),
    '2014': (r"(\b\d{7}\b)\s([\s\S]*?)(?=\b\d{7}\b|$)",r"CNPJ / CPF\s+([\d\.\/-]+)", r"EMISSÃO:\s*(\d{2}/\d{2}/\d{4})", r"Nº\.\s*\d+(\.\d+)*"),
    '2015': (r"(\b\d{7}\b)\s([\s\S]*?)(?=\b\d{7}\b|$)",r"CNPJ / CPF\s+([\d\.\/-]+)", r"EMISSÃO:\s*(\d{2}/\d{2}/\d{4})", r"Nº\.\s*\d+(\.\d+)*"),
    '2016': (r"(\b\d{7}\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"),
    # '2017': (r"(\b\d{7}\b)(.*?)-|(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})"),
    '2017': (r"(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"),
    '2018': (r"(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"),
    '2019': (r"(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"),
    '2020': (r"(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"),
    '2021': (r"(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)"),
    '2022': (r"(\b\d{7}-F\b)(.*?)-", r"CNPJ/CPF\s*\n*\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", r"DATA DE EMISSÃO\s*\n*\s*(\d{2}/\d{2}/\d{4})", r"N[º\.]\s*(\d+(\.\d+)?)")
}

class PDFTransformer:
    def __init__(self, filepath, year):
        self.filepath = filepath
        self.search_term = 'Valor Total: '
        self.output_file = 'tabela_produtos_%s_output.csv' % year
        self.year = year

    def extract_products(self):
        count = 0
        with open(self.filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            all_products = []
            for page in pdf_reader.pages:
                current_text = page.extract_text()
                if current_text:
                    current_text = current_text.replace('\n', ' ').replace('\r', ' ')
                    count += 1
                    # # print(f'Processing page {count}...')
                    # print(current_text)
                    current_nota_fiscal = self.find_nota_fiscal(current_text)
     
                    matching_products = self.extract_product_entries_from_page(current_text)
                    cnpj, date = self.extract_date_cnpj_from_page(current_text)
                    all_products.extend([(cnpj, date, product) for product in matching_products])
            return all_products

    def find_nota_fiscal(self, text):
        # Regular expression for the nota fiscal is 4th in the tuple
        pattern = RELATION_YEAR_REGEX[self.year][3]
        match = re.search(pattern, text)
        nota_fiscal = match.group(1) if match else None
        print(f'Found nota fiscal {nota_fiscal}')
        return nota_fiscal
    
    
    def extract_product_entries_from_page(self, text):
        products = []
        pattern = RELATION_YEAR_REGEX[self.year][0]
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        for match in matches:
            if self.year == '2017':
                # Special handling for 2017
                if match[0]:  # First pattern matched
                    number = match[0]
                    rest_of_string = match[1]
                else:  # Second pattern matched
                    number = match[2]
                    rest_of_string = match[3]
            else:
                # General handling for other years
                number = match[0]
                rest_of_string = match[1]

            try:
                product, values = self.extract_values_from_product(rest_of_string)
                # print(f'Found product {product} with values {values}')
                products.append((number, product, values))
            except Exception as e:
                # Handle or log the exception
                print(f"Error processing match: {e}")
        return products
        
    #get value from CNPJ / CPF until DATA DA EMISSÃO then date next to it
    def extract_date_cnpj_from_page(self, text):
        # Regular expression for CNPJ/CPF (this is a basic pattern, may need to adjust)
        cnpj_pattern = RELATION_YEAR_REGEX[self.year][1]
        cnpj_match = re.search(cnpj_pattern, text)
        cnpj = cnpj_match.group(1) if cnpj_match else None

        # Regular expression for the date
        date_pattern = RELATION_YEAR_REGEX[self.year][2]
        date_match = re.search(date_pattern, text)
        date = date_match.group(1) if date_match else None
        # print(f'Found CNPJ {cnpj} Date: {date}')
        return cnpj, date


    # Extract the product name and values from a product string
    def extract_values_from_product(self, product):
        # print(f'Extracting values from product: {product}')
        # Split the product string at 'CX'
        parts = product.split('CX')
        
        # Check if the split was successful and there are at least two parts
        if len(parts) < 2:
            #try to split at 'UN'
            parts = product.split('UN')
        if len(parts) < 2:
            #try to split at 'UNIDADE'
            parts = product.split('UNIDADE')
        if len(parts) < 2:
            #try to split at 'GF'
            parts = product.split('GF')
        
        if len(parts) >= 2:
            # The first part is the product name, and the second part contains the values
            product_name = parts[0].strip()
            values_part = parts[2] if self.year in ['2011', '2012', '2013', '2014', '2015'] and len(parts)>=3 else parts[1]
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
    # for product in products:
    #     print(product)
    #     print(type(product))
    HEADER = ['Nota Fiscal', 'Codigo Produto','Produto', 'Quantidade', 'Valor Unitário', 'Valor Total', 'CNPJ', 'Data']
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(HEADER)
        for product in products:
            try:
                codigo_produto = product[2][0] or ''
                produto = product[2][1] or ''
                quantidade = None
                valor_unitario = None
                valor_total = None
                if product[2][2] and len(product[2][2]) > 2:
                    quantidade = product[2][2][0]
                    valor_unitario = product[2][2][1]
                    valor_total = product[2][2][2]
                cnpj = product[0] or ''
                data = product[1] or ''
                writer.writerow([codigo_produto, produto, quantidade, valor_unitario, valor_total, cnpj, data])
            except:
                raise Exception('Error writing to CSV')
                pass


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
