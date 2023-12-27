import streamlit as st
from streamlit_option_menu import option_menu
from pdf2image import convert_from_path
import os, io
import pandas as pd
from google.cloud import vision
from PIL import Image
import fitz
from datetime import datetime
import pymongo
import requests
import re
import pytesseract

    
def extract_numbers(input_string):
    # Use regular expression to find all numeric substrings
    numbers = re.findall(r'\d+', input_string)
    
    # Convert the list of strings to a list of integers
    numbers = [int(num) for num in numbers]
    
    return numbers


client = pymongo.MongoClient('mongodb://localhost:27017/')

# create a database or use existing one
mydb = client['atl']

# create a collection
collection = mydb['records']

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "VisionAPI_ServiceAccountToken.json"
client = vision.ImageAnnotatorClient()

columns = ['Registration_no','Registration_date','First_registration_date','Makers_serial_no','Trade_maker_vehicle','Engine_model','Name_address','use','purpose','type_of_body','fixed_no','maxim_carry','weight','gweight','engine_capacity','fuel','length','width','height','export_schedule_day','mileage','approved']
df = pd.DataFrame(columns=columns)

def extract_capitals_and_numbers(input_string):
    return re.sub(r'[^A-Z0-9-]', '', input_string)

def date_format(input_date):
    # Define a dictionary to map Japanese numerals to Arabic numerals
    japanese_numerals = {
        '令和': 4,  # Adjust for the Reiwa era (2023 is in Reiwa era)
        '元': 1,
        '一': 1,
        '二': 2,
        '三': 3,
        '四': 4,
        '五': 5,
        '六': 6,
        '七': 7,
        '八': 8,
        '九': 9
    }

    # Input date string
    date_str = input_date

    # Use regular expressions to extract relevant parts of the date
    era = re.search(r'(\w+) (\d+)', date_str).group(1)  # Extract the era (e.g., 令和) and numeric year
    numeric_year = int(re.search(r'(\w+) (\d+)', date_str).group(2))  # Extract the numeric year
    month = int(re.search(r'(\d+) month', date_str).group(1))  # Extract the month
    day = int(re.search(r'(\d+) day', date_str).group(1))  # Extract the day

    # Adjust the year based on the era (2023 - 5 = 2018 in the Gregorian calendar)
    gregorian_year = 2018 + numeric_year

    # Format the date in "yyyy/mm/dd" format
    formatted_date = f"{gregorian_year}/{month:02d}/{day:02d}"

    return(formatted_date)

def image_crop(file_name):
    filepath = file_name
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]},)
    upper = response.text_annotations[0].bounding_poly.vertices[0].x +20
    left= response.text_annotations[0].bounding_poly.vertices[0].y
    im = Image.open(filepath)
    
    down =response.text_annotations[0].bounding_poly.vertices[2].y
    right =response.text_annotations[0].bounding_poly.vertices[2].x
    cropimg =(left,upper,right,down)
    im = im.crop(cropimg)
    extracted_data = pytesseract.image_to_osd(im)
    rotation_angle = int(extracted_data.split('\n')[1].split(':')[1].strip())
    im = im.rotate(rotation_angle, expand=True)

    im.save("new.png")
    
    return im

def pdf_to_png(pdf_bytes):
    pdf_document = fitz.open(stream=None, filetype="pdf")
    png_images = []

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        image = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        
        # Convert the Pixmap to PNG bytes
        png_bytes = io.BytesIO()
        image.get_image_data(output="png").write(png_bytes)
        png_bytes.seek(0)
        png_images.append(Image.open(png_bytes))

    return png_images
  



def text_extract(im):
    Registration_no =(13,72,360,110)
    value1 = im.crop(Registration_no)
    value1.save('v1.png')
    filepath = "v1.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    if texts:
        # Extract the description (text) from the first annotation
        Registration_no = texts[0].description.replace('\n',' ')
        Registration_no= re.sub(r'[~A-Z]', '', Registration_no)
    else:
        Registration_no = 'nil'
    
    Registration_date =(360,72,618,112)
    value2 = im.crop(Registration_date)
    value2.save('v2.png')
    filepath = "v2.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    if texts:
        Registration_date = texts[0].description.replace('\n',' ')
        try:
            Registration_date = date_format(Registration_date)
        except:
            Registration_date = extract_numbers(Registration_date)
            Registration_date = [str(Registration_date[i]) for i in range(1,len(Registration_date))]
            Registration_date= ("/".join(Registration_date))
            
    else:
        Registration_date ='nil'
    
    First_registration_date =(620,72,870,112)
    value3 = im.crop(First_registration_date)
    value3.save('v3.png') 
    filepath = "v3.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    # Check if there are text annotations
    if texts:
        First_registration_date = texts[0].description.replace('\n',' ')
        try:
            First_registration_date = date_format(First_registration_date)
        except:
            First_registration_date = extract_numbers(First_registration_date)
            First_registration_date = [str(First_registration_date[i]) for i in range(1,len(First_registration_date))]
            First_registration_date= ("/".join(First_registration_date))

    else:
        First_registration_date = 'nil'
    
    Makers_serial_no =(870,72,1340,110)
    value4 = im.crop(Makers_serial_no)
    value4.save('v4.png')
    filepath = "v4.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        Makers_serial_no = texts[0].description.replace('\n',' ')
        Makers_serial_no = re.sub(r'[^A-Z0-9-]', '', Makers_serial_no)
    else:
        Makers_serial_no='nil'
    
    Trade_maker_vehicle =(15,136,195,170)
    value5 = im.crop(Trade_maker_vehicle)
    value5.save('v5.png')
    filepath = "v5.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    if texts:
        Trade_maker_vehicle = texts[0].description.replace('\n',' ')
        Trade_maker_vehicle = re.sub(r'[A-Za-z0-9]', '', Trade_maker_vehicle)
    else:
        Trade_maker_vehicle ='nil'
    
    Engine_model =(1115,131,1360,170)
    value6 = im.crop(Engine_model)
    value6.save('v6.png')
    filepath = "v6.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        Engine_model = texts[0].description.replace('\n',' ')
        Engine_model = re.sub(r'[A-Z0-9-]', '', Engine_model)
    else:
        Engine_model='nil'
    Name_address =(192,175,715,255)
    value7 = im.crop(Name_address)
    value7.save('v7.png')
    filepath = "v7.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        Name_address = texts[0].description.replace('\n',' ')
    else:
        Name_address='nil'
    use =(194,415,264,457)
    value8 = im.crop(use)
    value8.save('v8.png')
    filepath = "v8.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        use = texts[0].description.replace('\n',' ')
        use = re.sub(r'[~A-Z0-9]', '', use)
    else:
        use='nil'
    purpose =(264,420,393,452)
    value9 = im.crop(purpose)
    value9.save('v9.png')
    filepath = "v9.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        purpose = texts[0].description.replace('\n',' ')
        purpose = re.sub(r'[~A-Z0-9]', '', purpose)
    else:
        purpose ='nil'
    type_of_body =(395,414,600,452)
    value10 = im.crop(type_of_body)
    value10.save('v10.png')
    filepath = "v10.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        type_of_body = texts[0].description.replace('\n',' ')
        type_of_body = re.sub(r'[~A-Za-z0-9]', '', type_of_body)
    else:
        type_of_body='nil'
    fixed_no =(800,415,860,459)
    value11 = im.crop(fixed_no)
    value11.save('v11.png')
    filepath = "v11.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        fixed_no = extract_numbers(texts[0].description.replace('\n',' '))
        fixed_no = ''.join(map(str, fixed_no))
    else:
        fixed_no ='nil'
    maxim_carry =(950,415,1058,455)
    value12 = im.crop(maxim_carry)
    value12.save('v12.png')
    filepath = "v12.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        maxim_carry = extract_numbers(texts[0].description.replace('\n',' '))
        maxim_carry = ''.join(map(str, maxim_carry))
    else:
        maxim_carry='nil'
    weight =(1100,415,1200,455)
    value13 = im.crop(weight)
    value13.save('v13.png')
    filepath = "v13.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        weight = extract_numbers(texts[0].description.replace('\n',' '))
        weight = ''.join(map(str, weight))
    else:
        weight='nil'
    gweight =(1315,415,1420,455)
    value14 = im.crop(gweight)
    value14.save('v14.png')
    filepath = "v14.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        gweight = extract_numbers(texts[0].description.replace('\n',' '))
        gweight = ''.join(map(str, gweight))
    else:
        gweight='nil'
    engine_capacity =(20,500,198,540)
    value15 = im.crop(engine_capacity)
    value15.save('v15.png')
    filepath = "v15.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        try:
            engine_capacity = extract_numbers(texts[0].description.replace('\n',' '))
            engine_capacity = ''.join(map(str, engine_capacity))
            engine_capacity = str(int(int(engine_capacity)*10))
        except:
            engine_capacity = texts[0].description.replace('\n',' ')



    else:
        engine_capacity='nil'
    fuel =(195,500,375,525)
    value16 = im.crop(fuel)
    value16.save('v16.png')
    filepath = "v16.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        fuel = texts[0].description.replace('\n',' ')
        fuel = re.sub(r'[~A-Za-z0-9]', '', fuel)
    else:
        fuel='nil'
    length =(730,500,862,535)
    value17 = im.crop(length)
    value17.save('v17.png')
    filepath = "v17.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        length =extract_numbers(texts[0].description.replace('\n',' '))
        length = ''.join(map(str, length))
    else:
        length ='nil'
    width =(863,500,960,533)
    value18 = im.crop(width)
    value18.save('v18.png')
    filepath = "v18.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        width = extract_numbers(texts[0].description.replace('\n',' '))
        width = ''.join(map(str, width))
    else:
        width='nil'
    height =(970,490,1068,535)
    value19 = im.crop(height)
    value19.save('v19.png')
    filepath = "v19.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        height = extract_numbers(texts[0].description.replace('\n',' '))
        height = ''.join(map(str, height))
    else:
        height='nil'
    export_schedule_day =(345,535,715,580)
    value20 = im.crop(export_schedule_day)
    value20.save('v20.png')
    filepath = "v20.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        export_schedule_day = texts[0].description.replace('\n',' ')
        try:
            export_schedule_day = date_format(export_schedule_day)
        except:
            export_schedule_day = extract_numbers(export_schedule_day)
            export_schedule_day = [str(export_schedule_day[i]) for i in range(1,len(export_schedule_day))]
            export_schedule_day= ("/".join(export_schedule_day))

    else:
        export_schedule_day='nil'
    mileage =(715,575,1315,615)
    value21 = im.crop(mileage)
    value21.save('v21.png')
    filepath = "v21.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        mileage = texts[0].description.replace('\n',' ')
    else:
        mileage='null'
    if len(mileage) ==4:
        date_of_application='abc'
    else:
        date_of_application =(45,800,600,815)
        value23 = im.crop(date_of_application)
        value23.save('v23.png')
        filepath = "v23.png"
        with io.open(filepath, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            date_of_application = texts[0].description.replace('\n',' ')
            try:
                date_of_application = date_format(date_of_application)
            except:
                date_of_application = extract_numbers(date_of_application)
                date_of_application = [str(date_of_application[i]) for i in range(1,len(date_of_application))]
                date_of_application= ("/".join(date_of_application))
                
        else:
            date_of_application='nil'
        
    if len(mileage) ==4:
        latest_owner = Name_address
    else:
        latest_owner =(30,722,670,758)
        value22 = im.crop(latest_owner)
        value22.save('v22.png')
        filepath = "v22.png"
        with io.open(filepath, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            latest_owner = texts[0].description.replace('\n',' ')
        else:
            latest_owner='nil'
    if len(mileage) ==4:
        mileage =(30,590,480,600)
        value21 = im.crop(mileage)
        value21.save('v21.png')
        filepath = "v21.png"
        with io.open(filepath, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            mileage = texts
        else:
            mileage='nil'
    serial_no =(123,19,360,45) 
    value23 = im.crop(serial_no)
    value23.save('v23.png') 
    
    filepath = "v23.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    # Check if there are text annotations
    if texts:
        # Extract the description (text) from the first annotation
        serial_no = extract_numbers(texts[0].description.replace('\n',' '))
        serial_no = ''.join(map(str, serial_no))
    else:
        serial_no = 'nil'
    model =(730,140,1100,165)  
    value25 = im.crop(model)
    value25.save('v25.png') 
    
    filepath = "v25.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    # Check if there are text annotations
    if texts:
        # Extract the description (text) from the first annotation
        model = texts[0].description.replace('\n',' ')
        model = re.sub(r'[^A-Z0-9-]', '', model)
    else:
        model = 'nil'
    ffweight =(1090,490,1170,530)
    value26 = im.crop(ffweight)
    value26.save('v26.png') 

    filepath = "v26.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    # Check if there are text annotations
    if texts:
        # Extract the description (text) from the first annotation
        ffweight = extract_numbers(texts[0].description.replace('\n',' '))
        ffweight = ''.join(map(str, ffweight))
    else:
        ffweight = 'nil'
    rrweight =(1370,490,1430,530)
    value27 = im.crop(rrweight)
    value27.save('v27.png') 

    filepath = "v27.png"
    with io.open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image,image_context={"language_hints": ["ja"]})
    texts = response.text_annotations
    # Check if there are text annotations
    if texts:
        # Extract the description (text) from the first annotation
        rrweight = extract_numbers(texts[0].description.replace('\n',' '))
        rrweight = ''.join(map(str, rrweight))
    else:
        rrweight = 'nil'


    approved ='no'
    return Registration_no,Registration_date,First_registration_date,Makers_serial_no,Trade_maker_vehicle,Engine_model,Name_address,use,purpose,type_of_body,fixed_no,maxim_carry,weight,gweight,engine_capacity,fuel,length,width,height,export_schedule_day,mileage,latest_owner,date_of_application,serial_no,model,ffweight,rrweight,approved


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def pdf_to_images(file_name):
     
# Convert PDF to images
    image = convert_from_path(file_name,200,poppler_path=r'C:\Program Files\new\poppler-23.10.0\Library\bin')
    abc = []
    for i in range(len(image)):
        extracted_data = pytesseract.image_to_osd(image[i])
        # Extract the rotation angle from the result
        rotation_angle = int(extracted_data.split('\n')[1].split(':')[1].strip())
        image[i] = image[i].rotate(rotation_angle, expand=True)
        image[i].save('page'+str(i)+'.png','PNG')
        abc.append(image[i])
    return abc



# SETTING PAGE CONFIGURATIONS

st.set_page_config(page_title= "Japanese Translator ",
                   
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# This app is extract japanese info from images"""})

tab1,tab2,tab3 = st.tabs(["$ Upload $", "$ Approve $","$ Analysis $"])
    # EXTRACT TAB
with tab1:
    st.markdown("#    ")
    st.write("### Upload Document :")
    def save_uploaded_file(uploaded_file):
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
    def main():
        i=0
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        if uploaded_file is not None:
            save_uploaded_file(uploaded_file)
            pdf_document = fitz.open("temp.pdf")
                            
            images=pdf_to_images('temp.pdf')
            
            for image in images:
                current_datetime = str(datetime.now()).replace(" ", "_").replace(":", "-")
                image.resize((1500, 1001)).save( f"{current_datetime}.png", "PNG")
                image = image_crop( f"{current_datetime}.png")
                upload_date =current_datetime
                a=text_extract(image)
                
                
                Registration_no,Registration_date,First_registration_date,Makers_serial_no,Trade_maker_vehicle,Engine_model,Name_address,use,purpose,type_of_body,fixed_no,maxim_carry,weight,gweight,engine_capacity,fuel,length,width,height,export_schedule_day,mileage,latest_owner,date_of_application,serial_no,model,ffweight,rrweight,approved = a
                data = {'Registration_no':Registration_no,'Registration_date':Registration_date,'First_registration_date':First_registration_date,'Makers_serial_no':Makers_serial_no,'Trade_maker_vehicle':Trade_maker_vehicle,'Engine_model':Engine_model,'Name_address':Name_address,'use':use,'purpose':purpose,'type_of_body':type_of_body,'fixed_no':fixed_no,'maxim_carry':maxim_carry,'weight':weight,'gweight':gweight,'engine_capacity':engine_capacity,'fuel':fuel,'length':length,'width':width,'height':height,'export_schedule_day':export_schedule_day,'mileage':mileage,'latest_owner':latest_owner,'date_of_application':date_of_application,'serial_no':serial_no,'model':model,'ffweight':ffweight,'rrweight':rrweight,'approved':approved,'image': f"{current_datetime}.png","upload_date":upload_date}
                try:
                    if Makers_serial_no:
                        #st.write("new data added in database")
                        client = pymongo.MongoClient('mongodb://localhost:27017/')
                        # create a database or use existing one
                        mydb = client['atl']
                        # create a collection
                        collection = mydb['records']
                        collection.insert_one(data)
                        client.close()
                    st.write("Transformation Successful!!!")
                except:
                    st.error(" Details already transformed!!")
            #os.remove("temp.pdf")  # Clean up temporary file
            
    # ...

    if __name__ == "__main__":
        main()
    
    #st.dataframe(data=df)


    #st.write(f'#### Extracted data from ')
    #st.table(ch_details)

    
# TRANSFORM TAB
with tab2:     
    st.markdown("#   ")
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['atl']
    collection = db['records']
    # Retrieve all documents in the collection
    
    condition = {"approved": "no"}

    cursor = collection.find(condition)
    documents = list(cursor)
    # Create a DataFrame from the list of dictionaries
    d1f = pd.DataFrame(documents)
    # Display the DataFrame
    #st.dataframe(d1f)
            
    # Get the count of documents
    document_count = len(documents)
    if document_count > 0:
        st.write(f"{document_count} document(s) waiting for 'approval':")
        for document in documents:
            
            projection = {'_id': 0, 'image': 1}
            cursor = collection.find(condition, projection)
            image_name = document.get('image', None)
            
            if image_name:
                    col1, col2, col3 = st.columns([0.6,0.2,0.2])
                                         

                    # Add content to each column
                    with col1:
                        fixed_column_content = st.image(image_name, width=None, output_format="PNG")
                    with col2:
                        Registration_no = st.text_input("Registration No", document.get('Registration_no', None),key = str({document['_id']})+'1')
                        Registration_date = st.text_input("Registration Date (yyyy/mm/dd)", document.get('Registration_date', None),key =str({document['_id']})+'2')
                        First_registration_date = st.text_input("First Registration Date (yyyy/mm)", document.get('First_registration_date', None),key = str({document['_id']})+'3')
                        Makers_serial_no = st.text_input("Makers Serial No", (document.get('Makers_serial_no', None)).replace(' ',''),key =str({document['_id']})+'4')
                        Trade_maker_vehicle = st.text_input("Trade Maker Vehicle", document.get('Trade_maker_vehicle', None),key =str({document['_id']})+'5')
                        Engine_model = st.text_input("Engine Model ", document.get('Engine_model', None),key =str({document['_id']})+'6')
                        Name_address = st.text_input("Name Address", document.get('Name_address', None),key =str({document['_id']})+'7')
                        use = st.text_input("Use", document.get('use', None),key = str({document['_id']})+'8')
                        purpose = st.text_input("Purpose", document.get('purpose', None),key=str({document['_id']})+'9')
                        type_of_body = st.text_input("Type of Body", document.get('type_of_body', None),key = str({document['_id']})+'10')
                        fixed_no = st.text_input("Fixed No (No of People)", document.get('fixed_no', None),key = str({document['_id']})+'11')
                        maxim_carry = st.text_input("Maxim Carry", document.get('maxim_carry', None),key = str({document['_id']})+'12')
                        model = st.text_input("Model",document.get('model',None),key =str({document['_id']})+'30')
                    with col3:
                        serial_no = st.text_input("Serial No", document.get('serial_no', None),key =str({document['_id']})+'24')
                        weight = st.text_input("Weight(Kg)", document.get('weight', None),key =str({document['_id']})+'13')
                        ffweight = st.text_input("FFWeight(Kg)", document.get('ffweight', None),key =str({document['_id']})+'31')
                        rrweight = st.text_input("RRWeight(Kg)", document.get('rrweight', None),key =str({document['_id']})+'32')
                        gweight = st.text_input("G-Weight(Kg)", document.get('gweight', None),key =str({document['_id']})+'14')
                        engine_capacity = st.text_input("Engine Capacity(CC)", document.get('engine_capacity', None),key =str({document['_id']})+'15')
                        fuel = st.text_input("Fuel", document.get('fuel', None),key = str({document['_id']})+'16')
                        length = st.text_input("Length (Cm)", document.get('length', None),key =str({document['_id']})+'17')
                        width = st.text_input("Width (Cm)", document.get('width', None),key =str({document['_id']})+'18')
                        height = st.text_input("Height (Cm)", document.get('height', None),key =str({document['_id']})+'19')
                        export_schedule_day = st.text_input("Export Schedule Day (yyyy/mm/dd)", document.get('export_schedule_day', None),key =str({document['_id']})+'20')
                        mileage = st.text_input("Mileage", document.get('mileage', None),key =str({document['_id']})+'21')
                        latest_owner = st.text_input("Latest Owner", document.get('latest_owner', None),key = str({document['_id']})+'22')
                        date_of_application = st.text_input("Date of Application (yyyy/mm/dd)", document.get('date_of_application', None),key =str({document['_id']})+'23')
                        upload_date = document.get('upload_date',None)
                        approve_date= str(datetime.now())
                        
                        approve = 'yes'
                    if st.button("Approve", key=str(document['_id'])+'25'):
                        
    # Update MongoDB record
                        
                        # Make a POST request to the API
                        try:
                            payload = {
                                "requestID": "CHASSISREQUEST",
                                "requestObject": {
                                    
                                    "Registration_no": Registration_no,
                                    "Registration_date": Registration_date,
                                    "First_registration_date": First_registration_date,
                                    "Makers_serial_no": Makers_serial_no,
                                    "Trade_maker_vehicle": Trade_maker_vehicle,
                                    "Engine_model": Engine_model,
                                    "Name_address": Name_address,
                                    "use": use,
                                    "purpose": purpose,
                                    "type_of_body": type_of_body,
                                    "fixed_no": fixed_no,
                                    "maxim_carry": maxim_carry,
                                    "weight": weight,
                                    "gweight": gweight,
                                    "engine_capacity": engine_capacity,
                                    "fuel": fuel,
                                    "length": length,
                                    "width": width,
                                    "height": height,
                                    "export_schedule_day": export_schedule_day,
                                    "mileage": mileage,
                                    "latest_owner": latest_owner,
                                    "date_of_application": date_of_application,
                                    "serial_no":serial_no,
                                    "upload_date":upload_date,
                                    "approve_date":approve_date,
                                    'model':model,
                                    'ffweight':ffweight,
                                    'rrweight':rrweight,
                                    "approved": 'yes'}
                                }
                            response = requests.post("https://atlapi.azurewebsites.net/api/chassisrequest", json=payload)
                            # Check if the request was successful
                            if response.status_code == 200:
                                response_data = response.json()
                                stock_id = response_data['responseObject']['StockId']
                                if stock_id == 0:
                                    st.success(f'Chassis number {Makers_serial_no} not found in stock table.')
                                else:
                                    st.success(f'Chassis number {Makers_serial_no} found in stock table.')
                                if stock_id ==100:
                                    st.success('Done')
                            else:
                                st.error("Try Again With Proper formated data")
                            filter_criteria = {'image': image_name}  # Replace with your actual filter criteria
                            # Specify the update operation
                            update_operation = {
                            '$set': {
                                'Registration_no': Registration_no,
                                'Registration_date': Registration_date,
                                'First_registration_date': First_registration_date,
                                'Makers_serial_no': Makers_serial_no,
                                'Trade_maker_vehicle': Trade_maker_vehicle,
                                'Engine_model': Engine_model,
                                'Name_address': Name_address,
                                'use': use,
                                'purpose': purpose,
                                'type_of_body': type_of_body,
                                'fixed_no': fixed_no,
                                'maxim_carry': maxim_carry,
                                'weight': weight,
                                'gweight': gweight,
                                'engine_capacity': engine_capacity,
                                'fuel': fuel,
                                'length': length,
                                'width': width,
                                'height': height,
                                'export_schedule_day': export_schedule_day,
                                'mileage': mileage,
                                'latest_owner': latest_owner,
                                'date_of_application': date_of_application,
                                'serial_no':serial_no,
                                'upload_date':upload_date,
                                'approve_date':approve_date,
                                'model':model,
                                'ffweight':ffweight,
                                'rrweight':rrweight,
                                'approved': 'yes'  # Assuming 'approved' field is updated to 'yes' during approval
                                }
                                }
                            # Update the documents
                            result = collection.update_many(filter_criteria, update_operation)
                        except requests.exceptions.RequestException as req_error:
                            st.error(f"Request exception: {str(req_error)}")
                    
                    if st.button("Delete",key=str({document['_id']})+'26'):
                        result = collection.delete_one({'image': image_name})
                        st.success('Successfully deleted {} document'.format(result.deleted_count))
                                    
    else:
        st.info("No un-approved records found.")

    
    
with tab3:
    st.markdown("#   ")
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['atl']
    collection = db['records']
    # Retrieve all documents in the collection
    approved = collection.count_documents({"approved": "yes"})

    pending = collection.count_documents({"approved": "no"})
    totall = collection.estimated_document_count()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.header("Approved ",divider='rainbow')
        st.header( approved)
    with col2:
        st.header("Pending ",divider='rainbow')
        st.header( pending)
    with col3:
        st.header('Total', divider='rainbow')
        st.header(totall)
                

