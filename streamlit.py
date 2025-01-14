import streamlit as st
import google.generativeai as genai
import json
import io
import fitz  # PyMuPDF for handling PDFs

# Configure Generative AI model
genai.configure(api_key="AIzaSyCpPsbTaLV9dya1iG0E_PbgmPiCA94CeUo")
st.title("PDF Image Analysis App")

st.markdown("""
### Analyze and Extract Key Information from PDF Images Effortlessly!
- **Upload a PDF file** to extract tables and essential details automatically.
- The app uses advanced AI-powered analysis to provide accurate and fast results.
- Please ensure your PDF contains images or scanned content for best results.
""")

# Initialize the generative model
model = genai.GenerativeModel("gemini-1.5-flash-8b")

# Allowed extension for uploaded files
ALLOWED_EXTENSION = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION

def extract_images_from_pdf(pdf_file):
    """
    Extracts images from each page of the given PDF file.
    Returns a list of images in byte format.
    """
    images = []
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            images_info = page.get_images(full=True)

            for img_index, img in enumerate(images_info):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                images.append(io.BytesIO(image_bytes))
    return images

def analyze_pdf_images(pdf_file):
    # Extract images from PDF
    extracted_images = extract_images_from_pdf(pdf_file)

    results = []
    prompt_template = """
    In this image, check if there's a table in the middle of the image. If yes, find these values from the table: company, authorization_code, cin, name, dob, diagnosis_code, date_from, date_to, phone, facility.
    After finding them, return the output in JSON format.

    Output format:
    {
        "company": "string",
        "authorization_code": "string",
        "cin": "string",
        "name": "string",
        "dob": "string",
        "diagnosis_code": "string",
        "date_from": "string",
        "date_to": "string",
        "phone": "string",
        "facility": "string"
    }

    Only output the JSON object with no additional text.
    """

    for image in extracted_images:
        try:
            uploaded_file = genai.upload_file(image, mime_type="image/png")

            # Generate content based on the uploaded file and the prompt
            result = model.generate_content([uploaded_file, prompt_template])
            result_text = result.text if hasattr(result, 'text') else result.choices[0].text

            # Extract valid JSON from the result
            start_index = result_text.find('{')
            end_index = result_text.rfind('}') + 1
            cleaned_result = result_text[start_index:end_index]

            # Parse the cleaned result into JSON
            extracted_values = json.loads(cleaned_result)
            results.append(extracted_values)
        except Exception as e:
            results.append({"error": f"Failed to process image: {str(e)}"})

    return results

# Streamlit UI

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    if allowed_file(uploaded_file.name):
        st.success("PDF file uploaded successfully! Processing...")
        with st.spinner("Analyzing images in the PDF... Please wait."):
            try:
                analysis_results = analyze_pdf_images(uploaded_file)
                st.success("Analysis complete! 🎉")
                st.json(analysis_results)
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
    else:
        st.error("Invalid file type. Please upload a valid PDF.")
else:
    st.info("Please upload a PDF file to begin analysis.")
