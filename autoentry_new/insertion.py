import oracledb
from main import create_connection
from fuzzywuzzy import fuzz
import api
from datetime import datetime

def fetch_supplier_code(supplier_name):
    connection,cursor=create_connection()
    cursor.execute("SELECT VC_SUPPLIER_NAME, NU_SUPPLIER_CODE FROM MST_SUPPLIER WHERE VC_COMP_CODE='01'")
    suppliers = cursor.fetchall()
    if not suppliers:
        return None
    matches = []
    # print(suppliers)
    for name in suppliers:
        # print(name)
        similarity_score = fuzz.ratio(name[0], supplier_name)
        if similarity_score>=92:
            matches.append((name, similarity_score))
    matches.sort(key=lambda x: x[1], reverse=True)
    if matches:
        return matches[0][0][1]
    else:
        return None

def existing(supplier_code,cursor,quote_no):
    
    cursor.execute(
                    """
                    SELECT CH_FAIL_STATUS 
                    FROM hd_supp_quote_temp 
                    WHERE VC_QUOTE_NO = :quote_no AND NU_SUPPLIER_CODE = :supplier_code
                    """,
                    quote_no=quote_no,
                    supplier_code=supplier_code
                )
    result = cursor.fetchone()
    if result:
        return result[0][0]
    else:
        return None

def insert_database(ans,cursor,supplier_code,ch_fail_status,output_pdf_path,pdf_name):
    try:

        quotation_date = ans["header"]["PI Date"]  # Example: '2024-12-17 11:05:56'

        try:
            # Convert the 'PI Date' string to a datetime object
            formatted_date = datetime.strptime(quotation_date, "%Y-%m-%d %H:%M:%S")  # Format: 'YYYY-MM-DD HH:MM:SS'
        except ValueError as e:
            formatted_date = None
        
        # If formatted_date is None, there was an issue with the date format
        if formatted_date:
            cursor.execute(
                """
                INSERT INTO hd_supp_quote_temp (
                    VC_COMP_CODE, NU_SUPPLIER_CODE, VC_SUPPLIER_NAME, VC_QUOTE_NO,
                    DT_QUOTE_DATE, VC_FIELD1, VC_FILE_NAME, PDF_DATA, DT_CREATE_DATE,
                    VC_MIME_TYPE, CH_STATUS, CH_FAIL_STATUS, NU_ID, NU_FIELD1, CH_IN_EX
                )
                VALUES (
                    '01', :supp_code, :SUPPLIER_NAME, :Quotation_no, TO_TIMESTAMP(:Quotation_date, 'YYYY-MM-DD HH24:MI:SS'),
                    curr_code(:currency1), :vc_file_name , :PDF_DATA, SYSDATE,
                    'application/pdf', 'P', :ch_fail_status, FILE_SEQUENCE.NEXTVAL, :total_value_of_quotation, :TAX_FLAG
                )
                """,
                supp_code=supplier_code,
                SUPPLIER_NAME=ans["header"]["Supplier Name"],
                Quotation_no=ans["header"]["PI No."],
                Quotation_date=formatted_date.strftime('%Y-%m-%d %H:%M:%S') if formatted_date else None,  # Convert back to string if needed
                currency1=ans["header"]["CURRENCY"],
                PDF_DATA=open(output_pdf_path, "rb").read(),
                vc_file_name=pdf_name,
                ch_fail_status=ch_fail_status,
                total_value_of_quotation=ans["Total"]["Total"],
                TAX_FLAG="E"
            )
            return "Data inserted successfully"
        else:
            return "Failed to insert due to invalid date format."

    except Exception as e:
        print(e)
        return "Encountered an error while inserting"
    
def insert_line_items(cursor,supplier_code,ans):
    try:
        for i in ans['line_items']:
            cursor.execute(
                            """
                            INSERT INTO dt_supp_quote_temp (
                                VC_COMP_CODE, NU_SUPPLIER_CODE, VC_SUPPLIER_NAME, VC_QUOTE_NO,
                                VC_ITEM_CODE, VC_ITEM_DESCRIPTION, NU_QTY, VC_FIELD1, NU_PRICE, NU_DISCOUNT,NU_FIELD1
                            )
                            VALUES (
                                '01', :supp_code, :SUPP_NAME, :QUOTATION_NO, :ITEM_CODE,
                                :item_description, :QTY, :unit, :PRICE, :discount,:TAX
                            )
                            """,
                            supp_code=supplier_code,
                            SUPP_NAME=ans['header']["Supplier Name"],
                            QUOTATION_NO=ans['header']["PI No."],
                            ITEM_CODE=i['Item Code'],
                            item_description=i["Item Description"],
                            QTY=i['Qty'],
                            unit=i["Unit"],
                            PRICE=i["Unit Price"],
                            discount=i["Disc.%"],
                            TAX=""
                        )
        return "Line Items Inserted Successfully"
    except Exception as e:
        print(e)
        return "Error While Inserting Line Items"