import zipfile
import xml.etree.ElementTree as ET
import sys
import os

docx_path = os.path.join(os.path.dirname(__file__), 'Project Family.docx')
if not os.path.exists(docx_path):
    # Try using the workspace path directly
    docx_path = r"C:\Users\elavi\Desktop\Project '' Family\Project Family.docx"

try:
    z = zipfile.ZipFile(docx_path)
    xml_content = z.read('word/document.xml')
    z.close()
    
    root = ET.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    texts = []
    for t in root.findall('.//w:t', ns):
        if t.text:
            texts.append(t.text)
    
    content = ''.join(texts)
    print(content.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)

