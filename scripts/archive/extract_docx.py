import zipfile
import xml.etree.ElementTree as ET
import sys

# Use the exact workspace path
workspace_path = r"C:\Users\elavi\Desktop\Project '' Family''"
docx_file = workspace_path + r"\Project Family.docx"

try:
    with zipfile.ZipFile(docx_file, 'r') as z:
        xml_content = z.read('word/document.xml')
    
    root = ET.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    texts = []
    for t in root.findall('.//w:t', ns):
        if t.text:
            texts.append(t.text)
    
    content = ''.join(texts)
    # Write to file to avoid encoding issues
    with open('docx_content.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Content extracted successfully to docx_content.txt")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

