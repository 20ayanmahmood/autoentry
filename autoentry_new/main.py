
from langchain_community.document_loaders import PyMuPDFLoader
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain.prompts import PromptTemplate
import json
import oracledb
import pytesseract
from datetime import datetime
from pdf2image import convert_from_path
import google.generativeai as genai
# path_to_tesseract=r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.pytesseract.tesseract_cmd=path_to_tesseract

# poppler_path = r'D:\poppler-windows-24.08.0-0\bin'

oracledb.init_oracle_client(lib_dir=r"D:\oracle\instantclient_23_5") 
os.environ['GOOGLE_API_KEY']=
os.environ['API_KEY'] = 
genai.configure(api_key=os.environ["API_KEY"])
llm=genai.GenerativeModel("gemini-1.5-flash",generation_config={"temperature":1})




"""<--------------------------------- Variables ------------------------------------------------------------>"""


header_aliases = {
    "Supplier Name": ["Supplier Name", "Vendor Name", "Party Name","Regards"],
    # "Supplied To":["supp To","supplied to"],
    "PI No.": ["PI No.", "Purchase Invoice No.", "Invoice No.","performa Invoice No."],
    "PI Date": ["PI Date", "Invoice Date", "Order Date"],
    "CURRENCY": ["CURRENCY", "Currency", "Payment Currency"],
    "Total"  :["Total:"," Total FOB","TOTAL (Inc VAT) :"]
}


line_item_aliases = {
    "Item Code": ["Item Code", "Code", "Product Code",'S N'],
    "Item Description": ["Item Description", "Description", "Product Description"],
    "Qty": ["Qty", "Quantity", "Ordered Quantity"],
    "Unit": ["Unit", "Unit Type", "Measurement Unit"],
    "Disc.%": ["Disc.%", "Discount Percentage", "Discount"],
    "Unit Price": ["Rate", "Price", "Unit Price"],
    "VAT" :["VAT","TAX"],
    "Total":["Total"]
    }

Total ={
    "Total Before Tax":["Total before tax"],
    "Total Discount": ["Total Disc"],
    "VAT Amount":["VAT","VAT Amount"],
    "Total":["Total"] 
}


"""<----------------------------------------------- Functions ---------------------------------------------->  """



def extract_text_from_image_pdf(pdf_path):
    """
    Extracts text from a PDF that contains images (scanned document) using OCR.

    Parameters:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF using OCR.
    """
    try:
        # Convert PDF pages to images
        images = convert_from_path(pdf_path)

        full_text = ""

        # Iterate over all the pages in the PDF (now images)
        for page_num, image in enumerate(images):
            print(f"Processing page {page_num + 1}...")

            # Use pytesseract to extract text from the image
            page_text = pytesseract.image_to_string(image)

            # Append the extracted text
            full_text += page_text
        
        return full_text

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def pdf_reader(file_path):
    loader = PyMuPDFLoader(file_path)
    pages = []
    async for page in loader.alazy_load():
        pages.append(page)
    return pages[0].page_content

def create_connection():
    connection = oracledb.connect(user='EBIZAI', password='EBIZAI', dsn="192.168.5.190:1521/ORCL") 
    print('Connection is established')
    cursor = connection.cursor()
    return connection, cursor   

def answer(file_path):
    template="""
    You are world class text reader based on given set of data : {pages}
    Your task is to extract the following field given based on these alias: {header_alias},{line_items_alias},{total}
    To clarify the supplier name below regards consist of supplier name.
    Date should be in : DD-MM-YYYY format
    And Only One Supplier name is allowed.
    And provide the Answer in given json format:
    Answer: provide answer based based on the given alias 
    { header:{"Supplier Name": "",
    "PI No.": ,
    "PI Date": ,
    "CURRENCY": ,
    "Total"  :},
        line_items:[{"Item Code": ,
    "Item Description": ,
    "Qty": , integer/float
    "Unit": ,
    "Disc.%":,integer/float
    "Unit Price": ,integer/float
    "VAT" :,integer/float
    "Total": ,integer/float
    }],
        Total:{    "Total Before Tax":,integer/float
    "Total Discount": ,integer/float
    "VAT Amount":,integer/float
    "Total": , integer/float"If total is not given caluclate it quanity * rate - ((qty * rate) * (discount / 100))"
    }"""

    sample_file = genai.upload_file(file_path, mime_type="application/pdf")
    contents = [sample_file, template]

    response = llm.generate_content(contents)
    print(response.text)
    answer=response.text
    
    # template="""
    # You are world class text reader based on given set of data : {pages}
    # Your task is to extract the following field given based on these alias: {header_alias},{line_items_alias},{total}
    # To clarify the supplier name below regards consist of supplier name.
    # Date should be in : DD-MM-YYYY format
    # And Only One Supplier name is allowed.
    # And provide the Answer in given json format:
    # Answer:
    # {{ header:{{}},
    #     line_items:{{}},
    #     Total:{{}},"If total is not given caluclate it quanity * rate - ((qty * rate) * (discount / 100))"
    # }}"""


    # prompt = PromptTemplate(template=template, input_variables=["pages","header_alias","line_items_alias","total"])
    # prompt_formatted_str = prompt.format(
    #     pages=pages, header_alias=str(header_aliases),line_items_alias=str(line_item_aliases),total=Total
    # )
    # answer = llm.predict(prompt_formatted_str)
    answer = answer.replace("```json", "").replace("```", "")
    answer=json.loads(answer)
    print(type(answer['header']['Supplier Name']))
    if answer['header']['Supplier Name'] is not None:
        answer['header']['Supplier Name']=(answer['header']['Supplier Name']).replace("TEAM","")
    return answer

# file_path=r"D:\New Folder\RAG\PDF\PI - 16304R.pdf"
# read=asyncio.run(pdf_reader(file_path))
# ans=answer(read)
# print(ans)
# print(type(ans))
# print(asyncio.run(pdf_reader(file_path)))
