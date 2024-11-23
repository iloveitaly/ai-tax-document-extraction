from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from decouple import config

AZURE_COGNITIVE_SERVICES_ENDPOINT = config(
    "AZURE_COGNITIVE_SERVICES_ENDPOINT", cast=str
)

AZURE_API_KEY = config("AZURE_API_KEY", cast=str)

# TODO set API version to altest

credential = AzureKeyCredential(AZURE_API_KEY)
document_intelligence_client = DocumentIntelligenceClient(
    AZURE_COGNITIVE_SERVICES_ENDPOINT, credential
)


# https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-tax-document?view=doc-intel-4.0.0#development-options
# TODO is there a literal for this in the package?
model_id = "prebuilt-tax.us.1099INT"

path_to_sample_documents = (
    "/path/to/document.pdf"
)

# Make sure your document's type is included in the list of document types the custom model can analyze
with open(path_to_sample_documents, "rb") as f:
    poller = document_intelligence_client.begin_analyze_document(
        model_id=model_id, analyze_request=f, content_type="application/octet-stream"
    )

result = poller.result()

# get all keys from the first document
result["documents"][0]["fields"].keys()

breakpoint()
