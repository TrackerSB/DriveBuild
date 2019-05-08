import os
import zipfile
from tempfile import mkdtemp
from lxml import etree
from werkzeug.datastructures import FileStorage

XSD_FILE = open("../schemes/drivebuild.xsd", "r")
SCHEMA_ROOT = etree.XML(XSD_FILE.read())
SCHEMA = etree.XMLSchema(SCHEMA_ROOT)
PARSER = etree.XMLParser(schema=SCHEMA)


def extract_test_cases(zip_file: FileStorage) -> str:
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    temp_dir = mkdtemp(prefix="drivebuild_")
    zip_ref.extractall(temp_dir)
    zip_ref.close()
    return temp_dir


def validate_test_cases(folder: str):
    for filename in os.listdir(folder):
        if filename.endswith(".dbe.xml") or filename.endswith(".dbc.xml"):
            xml_file = open(os.path.join(folder, filename), "r")
            try:
                root = etree.fromstring(xml_file.read(), PARSER)
            except etree.XMLSyntaxError as e:
                print(e)
