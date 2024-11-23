Current workflow

Accountant receive a PDF drop from a bunch of different brokerages and:

1. hand transcribe the data into wolters kluwer
2. hand mutate the PDFs to extract relevant attachments to the tax return
3. manually reorganize all of the files

the idea is you:

* Upload zip of all of the PDFs
* PDFs are reorganized in a standardized folder structure
* PDFs are analyzed to understand which pages are important
* Accountant can view high level analysis of all of the pages and information in each PDF
* W-2 and 1099-{B,DIV,INT,MISC} data is extracted
* Export templates are provided for multiple providers
* Download zip with reorganized files

## PDF Extraction

I'm working on the 1099 consolidated form ingestion. As I was going through it, I was wondering how you extract the brokerage transaction pages and attach them to the tax return. I remember you mentioning when we were talking that instead of including the detail in a reformatted page (like the old accountant), you extract the transaction detail and attach it to the PDF.

Part of why I'm curious about this is a feature that we could add is automatically extracting all of the transaction detail pages and slicing a PDF out.

In other words, once you are done with the tax return, you could request a transaction detail download. The system would go through all of the uploaded documents, find all of the transaction detail pages, create a cover page for each brokerage, and then include the original transaction detail PDFs in the downloaded zip / pdf file.

> Very interested!  Right now I run through the pdf broker statements and manually extract the pages. It takes a little bit of time but it totally worth not entering in the data.

## Azure Notes

* `az resource list --location eastus` will indicate that the resource group is `cpa-sidekick`
* Different parts of azure have their own little accounts: `az cognitiveservices account list`
* Once you have the name of the account, you can get the unique endpoint `az cognitiveservices account show --name "tax-document" --resource-group "cpa-sidekick" --query "properties.endpoint"`

### Document Intellegence

* Different model for each tax document type, you need to know the tax document type ahead of time
* Cannot intelligently determine which pages in a document are important, this needs to be determined beforehand. For instance, attempted to extract a 1099-B from the second page of transaction details.
* Response contains both the polygon content, full text analysis, and the document fields.
* If you input a PDF it will scan all pages but only return the pages it was able to find some content in the document.
* Fields available on the document are listed in `analyzeResult.documents[1].fields`
* Fields do not seem to be definitely documented for 1099, but are for some other documents.
* The model will only return the fields which it was able to get, will not return all available fields.