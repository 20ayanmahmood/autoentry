from fastapi import FastAPI, HTTPException,Form
from pydantic import BaseModel
import google.generativeai as genai
import os
from langchain_core.prompts import PromptTemplate
import json
from fastapi.middleware.cors import CORSMiddleware
# FastAPI initializati
import logging
from fastapi import FastAPI, HTTPException, Request,File, UploadFile
from fastapi.responses import JSONResponse
import pytesseract
from datetime import datetime
from main import pdf_reader,answer,create_connection,extract_text_from_image_pdf
import asyncio
from insertion import fetch_supplier_code,existing,insert_database,insert_line_items
from highlight import texts,highlight_text_with_debugging
import google.generativeai as genai

class UserRequest(BaseModel):
    user_id:str


class NameRequest(BaseModel):
    name:str

# logging.basicConfig(filename="logs/autoprompt.log",level=logging.INFO)
# logger = logging.getLogger(__name__)

app = FastAPI()
ans=None
logging.basicConfig(
    level=logging.INFO,  # Adjust logging level as needed (DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Log messages to a file
        logging.StreamHandler()          # Also print log messages to console
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)



# Helper function for storing the uploaded file
async def save_uploaded_file(file: UploadFile, save_path: str):
    try:
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"File {file.filename} saved to {save_path}")
    except Exception as e:
        logger.error(f"Error saving file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Error saving the uploaded file")
    

@app.post("/process_pdf")
async def process_pdf(user_id: str = Form(...), file: UploadFile = File(...)):
    try:

        logger.info(f"Processing PDF for user {user_id}...")

        upload_dir = os.path.join("pdf", user_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)

        # Save the uploaded file to the specified location
        await save_uploaded_file(file, file_path)

        # Read and process the PDF
        read = await pdf_reader(file_path)
        # logger.info(f"\n \n Reade File: {read} \n \n")
        ans = answer(file_path)
        logger.info(f"Answer extracted: {ans}")

        # Create output directory
        output_path = rf"D:\New Folder\autoentry_new\processed\{user_id}"
        os.makedirs(output_path, exist_ok=True)
        logger.info(f"Output directory created: {output_path}")

        # Process the extracted answer and highlight the text
        text = texts(ans)
        out = highlight_text_with_debugging(file_path, output_path + "\\idk.pdf", text)
        logger.info(f"Highlighted PDF saved at {output_path}\\idk.pdf")

        # Extract details from the answer
        name = ans['header']['Supplier Name']
        quote_no = ans['header']['PI No.']
        ans['header']['PI Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Connect to the database and check for existing data
        connection, cursor = create_connection()
        supp_code = fetch_supplier_code(name)
        exist = existing(supp_code, cursor, quote_no)
        
        # Determine fail status
        if not all([supp_code, quote_no, ans["header"]["PI Date"], ans["header"]["CURRENCY"]]):
            ch_fail_status = 'F'
            logger.warning("Some required fields are missing, setting fail status to 'F'")
        else:
            ch_fail_status = 'T'

        if exist == "T":
            logger.info("Data already exists, skipping the file processing")
            return {"message": "Data Existing Skipping The File", "ch_status": ch_fail_status}
        
        arr = insert_database(ans=ans, cursor=cursor, ch_fail_status=ch_fail_status,
                              output_pdf_path=out,
                              pdf_name=file.filename, supplier_code=supp_code)
        logger.info(f"Stored: {arr}")
        if arr == "Data inserted successfully":
            line = insert_line_items(cursor, supp_code, ans)
        else:
            line = "Not inserted as no suppliers found"  
        logger.info(f"Line Items : {line}")
        connection.commit()
        connection.close()
        logger.info("Database updated successfully \n \n") 
        return {"m1": arr, "m2": line}
    
    except Exception as e:
        logger.error(f"Error processing PDF for user {user_id}: {e} \n \n", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")        

    




