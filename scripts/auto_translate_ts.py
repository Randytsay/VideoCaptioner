import xml.etree.ElementTree as ET
import opencc
import sys

def translate_ts_file(ts_path, lang="zh_TW"):
    # "s2twp.json" converts Simplified to Traditional Chinese (Taiwan standard) with phrases.
    # "s2hk.json" for Hong Kong.
    converter = opencc.OpenCC('s2twp.json' if lang == "zh_TW" else 's2hk.json')
    
    tree = ET.parse(ts_path)
    root = tree.getroot()
    
    changed = 0
    for context in root.findall('context'):
        for message in context.findall('message'):
            source = message.find('source')
            translation = message.find('translation')
            
            if source is not None and translation is not None:
                # If the translation is empty or unfinished
                if translation.get('type') == 'unfinished' or not translation.text:
                    translated_text = converter.convert(source.text)
                    translation.text = translated_text
                    if 'type' in translation.attrib:
                        del translation.attrib['type']
                    changed += 1

    if changed > 0:
        tree.write(ts_path, encoding='utf-8', xml_declaration=True)
        print(f"[{ts_path}] Successfully updated {changed} strings to {lang}.")
    else:
        print(f"[{ts_path}] No strings needed translation.")

if __name__ == "__main__":
    translate_ts_file("resource/translations/VideoCaptioner_zh_HK.ts", "zh_HK")
    # if you also have TW
    # translate_ts_file("resource/translations/VideoCaptioner_zh_TW.ts", "zh_TW")
