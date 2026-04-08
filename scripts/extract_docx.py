import zipfile
import os

def extract_docx_xml(docx_path, output_xml):
    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            # Extract word/document.xml to output_xml
            xml_content = zip_ref.read('word/document.xml')
            with open(output_xml, 'wb') as f:
                f.write(xml_content)
            print(f"Successfully extracted document.xml to {output_xml}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    docx_path = r'd:\SPEECH_MECH3\SPEECH_MECH\Project Synopsis Format 2026.docx'
    output_xml = r'd:\SPEECH_MECH3\SPEECH_MECH\temp_document.xml'
    extract_docx_xml(docx_path, output_xml)
