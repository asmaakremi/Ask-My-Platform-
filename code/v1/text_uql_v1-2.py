from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import requests
from datetime import datetime, timezone
import re
#Rename the project to 3Dsearch_flask_NLQtoUQL
app = Flask(__name__)
CORS(app, origins=["http://localhost:8080", "https://vdevpril922dsy.dsone.3ds.com:444","https://ve4al631sy.dsone.3ds.com:444","https://dsext001-eu1-215dsi0708-ifwe.3dexperience.3ds.com"]) 

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def call_llm(prompt) :
    url = 'http://px101.prod.exalead.com:8110/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer vtYvpB9U+iUQwl0K0MZIj+Uo5u6kilAZJdgHGVBEhNc=',
        'Content-Type': 'application/json'
    }
    messages = [{"role": "user", "content": prompt}]
    payload = {
        "model":"mistralai/Codestral-22B-v0.1",
        "messages": messages,  
        "max_tokens": 500,
        "top_p": 1,
        "stop": ["string"],
        "response_format": {
            "type": "text", 
            "temperature": 0.7
        }
    }
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        generated_response = response.json()['choices'][0]['message']['content'].strip()
        return generated_response
    else:
        return f"Failed to generate response. Status code: {response.status_code}\nResponse: {response.text}"

    
def text_to_uql(query):
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    prompt = f"""
You are an expert in transforming natural language queries into UQL queries using a specified ontology. Based on user questions about data stored in an RDF graph, employ the provided ontology, documentation, and steps to understand the UQL syntax. Then, generate the UQL query equivalent for the given natural language query. The response should contain only the UQL query without any explanations or additional text.

** Current Date **: {current_date} (Use this date to handle queries involving specific time frames such as 'this year', 'today', etc., by calculating the relevant date ranges.)

** RDF Data Model and Ontology **
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix dsqt: <http://www.3ds.com/RDF/Corpus/dsqt/> .
    @prefix ds6w: <http://www.3ds.com/vocabularies/ds6w/> .
    @prefix ds6w1: <http://www.w3.org/2002/07/ds6w/> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix pno: <http://www.3ds.com/vocabularies/pno/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix swym: <http://www.3ds.com/vocabularies/swym/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    ds6w: a owl:Ontology ;
        rdfs:label "6W Vocabulary"@en ;
        rdfs:comment "This ontology defines the DS Corporate vocabulary for 6W tags."^^xsd:string ;
        owl:versionInfo "R2015x" .

    pno: a owl:Ontology ;
        rdfs:label "3DS PnO Vocabulary"@en ;
        rdfs:comment "This ontology defines the DS People and Organization vocabulary."^^xsd:string ;
        owl:versionInfo "R2016x" .
    
    swym: a owl:Ontology ;
        rdfs:label "3DSwym Vocabulary"@en ;
        rdfs:comment "This ontology defines 3DSwym vocabulary for 6W tags.Defines a social media structures including posts, ideas made within a social collaboration platform, potentially including metadata like user interactions, creation date and associated comments"^^xsd:string ;
        owl:versionInfo "R2016x" .

    VpmReference: a owl:Class ;
        rdfs:label "VpmReference"@en ;
        rdfs:comment "Physical Product archetype  .Represents physical products within the system and is equivalent to any general product classification. "@en .

    pno:Person rdf:type owl:Class ;
        rdfs:label "Person"@en ;
        rdfs:comment "Represents an individual person, detailing properties relevant to their role and activities within an organization."@en .
    
    PhysicalProduct rdf:type owl:Class ;
        owl:equivalentClass VPMReference .

    Product rdf:type owl:Class ;
        owl:equivalentClass VPMReference .

    Document rdf:type owl:Class ;
        rdfs:comment "General class for documents."@en .

    SocialContent rdf:type owl:Class ;
        rdfs:comment "Content generated in social platforms, like posts, comments, or likes."@en .
    
    PLMDMT_DocCustom rdf:type owl:Class ;
        rdfs:subClassOf Document ;
        rdfs:comment "A customized document type within the PLM system."@en .

    PLMDMTDocument rdf:type owl:Class ;
        rdfs:subClassOf Document ;
        rdfs:comment "A standard document type for engineering documents within the PLM system."@en .

    3DShape rdf:type owl:Class ;
        rdfs:comment "Represents a 3D shape model in the system."@en .
    
    swym:Post rdf:type owl:Class ;
        rdfs:subClassOf SocialContent ;
        rdfs:comment "A post within the social collaboration platform."@en .
    
    swym:Idea rdf:type owl:Class ;
        rdfs:subClassOf SocialContent ;
        rdfs:comment "an idea within the social collaboration platform."@en .

    BusinessRoleClass rdf:type owl:Class;
        rdfs:label "Business Role Class"@en;
        rdfs:comment "Defines various business roles that can be held by persons within the organization, such as Vice President, Engineer, etc. these instance of the class are values to the property ds6w:businessRole"@en.

    :StrategyAndManagement rdf:type BusinessRoleClass;
        rdfs:label "Strategy & Management"@en.
        rdfs:comment "Primary class representing a strategic management role of a person within the organization."@en.

    :VicePresident rdf:type :BusinessRoleClass;
        rdfs:comment "Role equivalent to Strategy & Management."@en;
        owl:equivalentClass :StrategyAndManagement.

    :Engineer rdf:type BusinessRoleClass;
        rdfs:label "Engineer"@en.

    :SoftwareEngineer rdf:type BusinessRoleClass;
        rdfs:label "Software Engineer"@en.

    :DataScientist rdf:type BusinessRoleClass;
        rdfs:label "Data Scientist"@en.

    ds6w:type rdf:type owl:DatatypeProperty;
        rdfs:label "Type"@en;
        rdfs:comment "Specifies the type of object."@en;
        rdfs:domain [ rdf:unionOf (PLMDMT_DocCustom PLMDMTDocument AecMember pno:Person vpmReference:VPMReference Document 3DShape swym:Post swym:Idea ) ];
        rdfs:range xsd:string.
    
    ds6w:modified rdf:type owl:DatatypeProperty;
        rdfs:label "Modified"@en;
        rdfs:comment "Date and time of last modification. Expected format: 'YYYY-MM-DD'T'hh:mm:ss'Z' (ISO 8601)"@en;
        rdfs:domain [ rdf:unionOf (PLMDMT_DocCustom PLMDMTDocument AecMember vpmReference:VPMReference Document 3DShape swym:Post swym:Idea ) ];
        rdfs:range xsd:dateTime.
    
    ds6w:created rdf:type owl:DatatypeProperty;
        rdfs:label "Created"@en;
        rdfs:comment "Date and time of last modification. Expected format: 'YYYY-MM-DD'T'hh:mm:ss'Z' (ISO 8601)"@en;
        rdfs:domain [ rdf:unionOf (PLMDMT_DocCustom PLMDMTDocument AecMember vpmReference:VPMReference Document 3DShape swym:Post swym:Idea ) ];
        rdfs:range xsd:dateTime.
    
    ds6w:lastModifiedBy rdf:type owl:ObjectProperty;
        rdfs:label "Last Modified By"@en;
        rdfs:comment "Specifies the last person  pno:Person who modified an entity. This property is used for tracking modifications to documents, products, or any other entities within the system."@en;
        rdfs:domain [ rdf:unionOf (PLMDMT_DocCustom PLMDMTDocument AecMember vpmReference:VPMReference Document 3DShape swym:Post swym:Idea ) ];
        rdfs:range pno:Person.
    
    ds6w:responsible rdf:type owl:ObjectProperty;
        rdfs:label "Responsible"@en;
        rdfs:comment "Indicates name of the person pno:Person responsible for a particular entity, such as a document or product. Use this property to find entities based on the accountability of individuals.To identify the person responsible for a specific object: [ds6w:responsible]:'instance of pno:Person'"@en.        rdfs:domain [ rdf:unionOf (PLMDMT_DocCustom PLMDMTDocument AecMember vpmReference:VPMReference Document 3DShape swym:Post swym:Idea ) ];
        rdfs:range pno:Person.
    
    ds6w:Comments rdf:type owl:DatatypeProperty;
        rdfs:label "Comments"@en;
        rdfs:comment "Number of comments for the post, idea or any subtype of social content."@en;
        rdfs:domain  [ rdf:unionOf(swym:Post swym:Idea)] ;
        rdfs:range xsd:integer.
    
    ds6w:endorsements rdf:type owl:DatatypeProperty;
        rdfs:label "Likes"@en;
        rdfs:comment "Number of Likes for the post or idea or any subtype of social content."@en;
        rdfs:domain [ rdf:unionOf (swym:Post swym:Idea)] ;
        rdfs:range xsd:integer.
    
    ds6w:contentStructure rdf:type owl:DatatypeProperty;
        rdfs:label "Content Structure"@en;
        rdfs:comment "Specifies the hierarchical content structure exclusively for VPMReferences and 3DShape.";
        rdfs:domain [ rdf:unionOf (VPMReference 3DShape) ];
        rdfs:range xsd:string;
        owl:oneOf ("Root" "Leaf" "Intermediate" "Standalone").
    
    ds6w:docExtension rdf:type owl:DatatypeProperty;
        rdfs:label "Document Extension"@en;
        rdfs:comment "The file format of the document, restricted to specific extensions.jpg for images, docx or txt for text,pdf for pdf files etc."@en;
        rdfs:domain [ rdf:unionOf (PLMDMT_DocCustom PLMDMTDocument Document ) ];
        rdfs:range xsd:string;
        owl:oneOf ("jpg" "idx" "docx" "pdf" "stp" "xls" "doc" "txt").
    
    ds6w:BusinessRole rdf:type owl:ObjectProperty;
        rdfs:label "Business Role"@en;
        rdfs:comment "Links a person to their business role within the organization. Use this property to query for individuals based on their specific organizational roles for example a Vp person have  StrategyAndManagement as business role ."@en;
        rdfs:domain pno:Person;
        rdfs:range BusinessRoleClass.

    ds6w:description a owl:DatatypeProperty ;
        rdfs:label "Description"@en ;
        rdfs:comment "Description of an object, for example object about a topic  "@en ;
        rdfs:range xsd:string ;

    ds6w:label a owl:DatatypeProperty ;
        rdfs:label "Title"@en ;
        rdfs:comment "Label or the title of an object   "@en ;
        rdfs:range xsd:string ;
    
    # Example triple : 
    pno:person123 rdf:type pno:Person ;
        pno:name "person123" ;
        ds6w:businessRole "Strategy & Managemenent" ;

    pno:person124 rdf:type pno:Person ;
        pno:name "person124" ;
        ds6w:businessRole "Data Scientist" ;

    :doc001 rdf:type Document ;
        ds6w:type "PLMDMTDocument" ;
        ds6w:docExtension "pdf" ;
        ds6w:created "2024-06-01T00:00:00Z"^^xsd:dateTime ;
        ds6w:modified "2024-06-05T00:00:00Z"^^xsd:dateTime ;
        ds6w:responsible person123 ;
        ds6w:lastModifiedBy person124 ;

    :product01 rdf:type VpmReference ;
        ds6w:type "VpmReference" ;
        ds6w:created "2024-06-01T00:00:00Z"^^xsd:dateTime ;
        ds6w:modified "2024-06-05T00:00:00Z"^^xsd:dateTime ;
        ds6w:responsible person123 ;
        ds6w:lastModifiedBy person124 ;
        ds6w:contentStructure "Root".

    swym:post001 rdf:type swym:Post ;
        ds6w:Comments 5 ;
        ds6w:endorsements 10.
        ds6w:lastModifiedBy person124 ;
        ds6w:label Ai;

    swym:idea001 rdf:type swym:Idea ;
        ds6w:Comments 4 ;
        ds6w:endorsements 1.
        ds6w:lastModifiedBy person124 ;
        ds6w:responsible person124 ;

### Example UQL Queries:
1. **Natural Language**: "give me products that are created between 2024-05-01 to 2024-05-28 by MCM OCDxComplianceUser"
   - **UQL**: `[ds6w:created]>="2024-05-01T00:00:00.000Z" AND [ds6w:created]<="2024-05-28T23:59:59.000Z" AND [ds6w:type]:"VPMReference" AND (([ds6w:lastModifiedBy]:"MCM OCDxComplianceUser" OR [ds6w:responsible]:"MCM OCDxComplianceUser"))`

2. **Natural Language**: "search for posts created by enopotionuser01 having number of likes or comments =2 AND likes > 0"
   - **UQL**: `[ds6w:type]:"swym:Post" AND [ds6w:responsible]:"enopotionuser01" AND [ds6w:comments]:2 AND [ds6w:endorsements]:>0`

3. **Natural Language**: "give me all documents created by a vp"
   - **UQL**: `[ds6w:type]:"Document" AND [ds6w:businessRole]:"Strategy & Management"`

### Conversion Steps:
1. **Identify Key Components**: Analyze the natural language query to determine the main entity (subject), properties (predicates), and values (objects).
2. **Map to RDF Concepts**: Use the ontology to correlate the identified natural language elements with RDF classes and predicates.
3. **Construct the UQL Query**: Synthesize the mapped elements into a UQL query following the defined syntax, ensuring alignment with the RDF ontology structure. If a term is not mapped, assign it to the property [ds6w:label] or  [ds6w:description].

### Example UQL Query Construction:
**Natural Language Query**: "Show me all documents created on January 1, 2020, by John Doe about AI."
1. **Parse the Natural Language Query**:
   - Subject: Documents
   - Predicate: Created by and date of creation
   - Object: John Doe and January 1, 2020
2. **Map to RDF Concepts**:
   - Documents: Instances of the 'Document' class.
   - Created by: 'ds6w:lastModifiedBy' or 'ds6w:responsible'.
   - Date of creation: 'ds6w:created'.
   - John Doe: Instances of the 'Person' class.
   - About AI: Use 'ds6w:label' or 'ds6w:description'.
3. **Formulate the UQL Query**:
   - `[ds6w:label]:ai OR [ds6w:description]:ai AND [ds6w:type]:"Document" AND [ds6w:created]>="2020-01-01T00:00:00.000Z" AND ([ds6w:lastModifiedBy]:"John Doe" OR [ds6w:responsible]:"John Doe")`

### Specific Instructions:
   - When the query specifies a role or position within the organization, use the `BusinessRole` property.
   - When the query refers to individuals in general without specifying their role, use `[ds6w:type]:pno:Person`.
   - If a term does not directly map to any defined class or property, use `ds6w:label`property to handle such terms.

** Generate UQL Query:**
Based on the natural language query "{query}" and the current date if needed, generate the corresponding UQL query using the ontology and RDF relationships. Ensure the output strictly adheres to the syntax and ontology requirements without adding or assuming types not explicitly defined.

Respond ONLY with the valid UQL query.
"""
    try:
        return call_llm(prompt), prompt
    except Exception as e:
        return str(e) 

def get_reflection_for_uql(full_prompt, llm_response, errors):
    reflection_prompt = f"""
    You were given the following prompt:

    {full_prompt}

    Your UQL conversion was:

    {llm_response}

    Here are the list of the errors in your conversion. Please review your UQL query and correct it:

    {' '.join(errors)}
    """
    corrected_uql = call_llm(reflection_prompt)
    return corrected_uql

def validate_uql_response(uql_response):
    corrected = uql_response
    error_messages = []
    rdf_properties = [
        'ds6w:created', 'ds6w:modified', 'ds6w:type', 'ds6w:lastModifiedBy', 'ds6w:responsible', 'ds6w:BusinessRole', 
        'ds6w:contentStructure','ds6w:docExtension','ds6w:endorsements','ds6w:Comments',
    ]
    allowed_type_values = [
        'PLMDMT_DocCustom', 'PLMDMTDocument', 'AecMember', 'pno:Person', 
        'VPMReference', 'Document', '3DShape', 'swym:Post','swym:Idea'
    ]

    # invalid_value_pattern = r'\[\w+:\w+\]:"(?|)"'
    # invalid_values = re.findall(invalid_value_pattern, corrected)
    # # If invalid values are found
    # if invalid_values:
    #     error_messages.append("Error: Invalid or empty value found.")
    #     # logging.error("Invalid or empty value found: %s", invalid_values)
    # # Validate empty or invalid value comparisons
    invalid_value_pattern = r'\[\w+:\w+\](<>"\\"")'
    invalid_values = re.findall(invalid_value_pattern, uql_response)
    if invalid_values:
        error_messages.append("Error: Invalid or empty value comparisons found.")
        logging.error("Invalid or empty value comparisons found: %s", invalid_values)

    # Check attributes surrounded by incorrect parentheses
    for prop in rdf_properties:
        pattern = rf'\({prop}\)'
        if re.search(pattern, corrected):
            corrected = re.sub(pattern, f'[{prop}]', corrected)
            error_messages.append(f"Error: {prop} should be surrounded by square brackets []. Correction applied.")
            logging.info("%s was surrounded by incorrect brackets, correction applied.", prop)

    # Validate [ds6w:type] values
    type_errors = []
    type_matches = re.findall(r'\[ds6w:type\]:"([^"]+)"', corrected)
    for type_value in type_matches:
        if type_value not in allowed_type_values:
            type_errors.append(type_value)
    if type_errors:
        error_message = ("Error: Invalid type values for [ds6w:type]. The value must be in the list of "
                     f"{allowed_type_values}. Please choose the appropriate type based on the intent of the NLQ "
                     "and avoid adding unauthorized types.")
        error_messages.append(error_message)
        logging.warning("Invalid type values detected: %s", type_errors)

    # Correct unnecessary spaces around colons
    spaces_around_colons = re.findall(r'\[\w+\]\s*:\s*\"[^\"]+\"', corrected)
    for item in spaces_around_colons:
        corrected_item = re.sub(r'\s*:\s*', ':', item)
        corrected = corrected.replace(item, corrected_item)
    if spaces_around_colons:
        error_messages.append("Error: Unnecessary spaces found around colons.")
        logging.info("Unnecessary spaces around colons corrected.")

    # Check datetime format
    datetime_format_errors = []
    for attr in ['created', 'modified']:
        datetime_matches = re.findall(rf'\[ds6w:{attr}\]:"([^"]+)"', corrected)
        datetime_format_errors.extend(
            [match for match in datetime_matches if not re.match(r'\d{4}-\d{2}-\d{2}T00:00:00\.000Z', match)]
        )
    if datetime_format_errors:
        error_messages.append("Error: Invalid datetime format.")
        logging.error("Invalid datetime formats found: %s", datetime_format_errors)

    # Detect incorrect operator usage
    error_pattern = r'\[ds6w:[^\]]+\](?![>=<: ])([^"]+)"'
    errors = re.findall(error_pattern, corrected)
    if errors:
        error_messages.append("Error: Incorrect operator usage detected.")
        logging.error("Incorrect operator usage detected: %s", errors)

    return error_messages, corrected, bool(error_messages)

@app.route('/sophisticated_query', methods=['POST'])
def query_uql():
    data = request.get_json(force=True)
    user_query = data.get('query')
    print("query", user_query)
    while True:
        uql_query, uql_prompt = text_to_uql(user_query)
        errors, corrected_uql, has_errors = validate_uql_response(uql_query)
        if has_errors:
            logging.error("Errors detected: %s", errors)
            final_uql_query = get_reflection_for_uql(uql_prompt, corrected_uql, errors)
            user_query = final_uql_query  
        else:
            logging.info("No errors found, returning valid UQL.")
            logging.info("Response",corrected_uql)
            return jsonify({"response": corrected_uql})

if __name__ == '__main__':
    app.run(debug=True)