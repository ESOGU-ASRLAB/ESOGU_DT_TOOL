import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

def convert_uml_to_xml(input_path: str) -> str:
    """
    PlantUML .uml dosyasını okuyup okunabilir (pretty) XML string olarak döndürür.
    """
    with open(input_path, 'r') as f:
        lines = f.readlines()

    root = ET.Element('UMLModel')

    # Parse class declarations
    classes = {}
    class_def_pattern = re.compile(r'\s*class\s+(\w+)\s*<<(\w+)>>\s*\{')
    for line in lines:
        m = class_def_pattern.match(line)
        if m:
            name, stereotype = m.groups()
            cls_elem = ET.SubElement(root, 'Class', {'name': name, 'stereotype': stereotype})
            classes[name] = cls_elem

    # Parse attributes and methods within classes
    current_class = None
    for line in lines:
        start = class_def_pattern.match(line)
        if start:
            current_class = classes[start.group(1)]
            continue
        if current_class and line.strip() == '}':
            current_class = None
            continue
        if not current_class:
            continue

        content = line.strip()
        # Method pattern: + name(params): returnType
        method_pattern = re.compile(r'([+-])\s*(\w+)\(([^)]*)\):\s*(\w+)')
        m = method_pattern.match(content)
        if m:
            visibility, name, params, return_type = m.groups()
            method_elem = ET.SubElement(current_class, 'Method', {'name': name, 'visibility': visibility, 'returnType': return_type})
            params_elem = ET.SubElement(method_elem, 'Parameters')
            if params:
                for param in params.split(','):
                    pname, ptype = param.strip().split(':')
                    ET.SubElement(params_elem, 'Parameter', {'name': pname.strip(), 'type': ptype.strip()})
            continue

        # Attribute pattern: + name: type
        attr_pattern = re.compile(r'([+-])\s*(\w+):\s*(\w+)')
        m = attr_pattern.match(content)
        if m:
            visibility, name, type_ = m.groups()
            ET.SubElement(current_class, 'Attribute', {'name': name, 'visibility': visibility, 'type': type_})

    # Parse relationships (inheritance and associations)
    for line in lines:
        inh_pattern = re.compile(r'\s*(\w+)\s*--\|>\s*(\w+)')
        m = inh_pattern.match(line)
        if m:
            subclass, superclass = m.groups()
            ET.SubElement(root, 'Inheritance', {'subclass': subclass, 'superclass': superclass})
            continue

        assoc_pattern = re.compile(r'\s*(\w+)\s*"([^"]+)"\s*--\s*"([^"]+)"\s*(\w+)\s*:\s*(\w+)')
        m = assoc_pattern.match(line)
        if m:
            class1, mult1, mult2, class2, name = m.groups()
            assoc_elem = ET.SubElement(root, 'Association', {'name': name})
            ET.SubElement(assoc_elem, 'End', {'class': class1, 'multiplicity': mult1})
            ET.SubElement(assoc_elem, 'End', {'class': class2, 'multiplicity': mult2})

    # XML string olarak pretty-print döndür
    rough_string = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')


# Örnek kullanım kaldırıldı, dosya yazma yok.