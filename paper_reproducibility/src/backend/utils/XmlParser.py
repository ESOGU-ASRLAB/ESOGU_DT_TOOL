import xml.etree.ElementTree as ET
import json

def parse_uml_xml_to_json(xml_content):
    root = ET.fromstring(xml_content)

    uml_model = {
        "name": root.attrib.get('Name', 'Unknown'),
        "version": root.attrib.get('UmlVersion', '2.x'),
        "classes": [],
        "relationships": []
    }

    id_to_classname = {}
    added_class_names = set()

    # Sadece <Models> altındaki doğrudan <Class> elemanlarını al
    models = root.find(".//Models")
    if models is not None:
        for cls in models.findall("./Class"):
            class_name = cls.attrib.get('Name', 'unnamed')
            class_id = cls.attrib.get('Id')
            if not class_id:
                continue
            id_to_classname[class_id] = class_name

        for cls in models.findall("./Class"):
            class_name = cls.attrib.get('Name', 'unnamed')
            class_id = cls.attrib.get('Id')
            if not class_id or class_name in added_class_names:
                continue
            visibility = cls.attrib.get('Visibility', 'public')

            class_dict = {
                "name": class_name,
                "visibility": visibility,
                "attributes": [],
                "operations": []
            }

            # Nitelikler
            model_children = cls.find("ModelChildren")
            if model_children is not None:
                for attr in model_children.findall("Attribute"):
                    attr_name = attr.attrib.get('Name', 'unnamed')
                    attr_visibility = attr.attrib.get('Visibility', 'private')
                    class_dict["attributes"].append({
                        "name": attr_name,
                        "visibility": attr_visibility
                    })
                for op in model_children.findall("Operation"):
                    op_name = op.attrib.get('Name', 'unnamed')
                    op_visibility = op.attrib.get('Visibility', 'public')
                    class_dict["operations"].append({
                        "name": op_name,
                        "visibility": op_visibility
                    })

            uml_model["classes"].append(class_dict)
            added_class_names.add(class_name)

    # İlişkileri <ModelRelationshipContainer> içinden analiz et
    rel_root = root.find(".//ModelRelationshipContainer[@Name='relationships']")
    if rel_root is not None:
        for rel_type_container in rel_root.findall("ModelChildren/ModelRelationshipContainer"):
            rel_type = rel_type_container.attrib.get("Name", "Unknown")
            for rel in rel_type_container.findall("ModelChildren/*"):
                # İlişki tipi (Generalization, Usage, Association)
                from_id = rel.attrib.get("From")
                to_id = rel.attrib.get("To")
                # Association'da From/To yok, EndRelationshipFromMetaModelElement/EndRelationshipToMetaModelElement var
                if rel.tag == "Association":
                    from_id = rel.attrib.get("EndRelationshipFromMetaModelElement")
                    to_id = rel.attrib.get("EndRelationshipToMetaModelElement")
                from_class = id_to_classname.get(from_id, from_id)
                to_class = id_to_classname.get(to_id, to_id)
                rel_dict = {
                    "type": rel_type,
                    "from": from_class,
                    "to": to_class
                }
                # Usage için stereotype ekle
                if rel.tag == "Usage":
                    stereotype = ""
                    stereotypes = rel.find("Stereotypes")
                    if stereotypes is not None:
                        st = stereotypes.find("Stereotype")
                        if st is not None:
                            stereotype = st.attrib.get("Name", "")
                    rel_dict["stereotype"] = stereotype
                uml_model["relationships"].append(rel_dict)

    return uml_model
