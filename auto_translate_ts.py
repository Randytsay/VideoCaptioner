import sys
import xml.etree.ElementTree as ET
import opencc

def translate_ts(file_path):
    converter = opencc.OpenCC('s2hk')
    tree = ET.parse(file_path)
    root = tree.getroot()

    count = 0
    for message in root.findall('.//message'):
        source = message.find('source')
        translation = message.find('translation')
        
        if source is not None and translation is not None:
            # 如果 translation 為空或與 source 相同且包含中文字符，則進行翻譯
            source_text = source.text if source.text else ""
            
            # 使用 OpenCC 進行轉換
            translated_text = converter.convert(source_text)
            
            if translation.text != translated_text:
                translation.text = translated_text
                translation.attrib.pop('type', None) # 移除 'unfinished' 標籤
                count += 1

    tree.write(file_path, encoding='utf-8', xml_declaration=True)
    print(f"Successfully translated {count} messages.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_translate_ts.py <path_to_ts_file>")
    else:
        translate_ts(sys.argv[1])
