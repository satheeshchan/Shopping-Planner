import fitz  # PyMuPDF
import os

def extract_text_from_pdf(pdf_path: str) -> str | None:
    """
    Extracts all text content from a given PDF file.

    Args:
        pdf_path: The file path to the PDF.

    Returns:
        A string containing all extracted text from the PDF,
        or None if an error occurs (e.g., file not found, corrupted PDF).
    """
    if not os.path.exists(pdf_path):
        # print(f"Error: PDF file not found at {pdf_path}") # For server-side logging
        return None
    
    try:
        document = fitz.open(pdf_path)
        full_text = []
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            full_text.append(page.get_text("text")) # "text" for plain text extraction
        
        document.close()
        return "\n".join(full_text)
    except Exception as e:
        # print(f"Error processing PDF {pdf_path}: {e}") # For server-side logging
        # Depending on the desired error handling, you might want to log the specific error
        # or return a more specific error message. For now, returning None indicates failure.
        return None

if __name__ == '__main__':
    # This section is for testing the pdf_processor.py directly.
    # You would need to place a sample PDF in the script's directory or provide a full path.
    print("Running a direct test of pdf_processor.py...")
    
    # Create a dummy PDF for testing if one doesn't exist
    # Note: This creates a very simple PDF. For robust testing, use diverse real-world PDFs.
    sample_pdf_path = "sample_test.pdf"
    if not os.path.exists(sample_pdf_path):
        try:
            doc = fitz.open() # new empty PDF
            page = doc.new_page()
            page.insert_text((50, 72), "Hello, this is a test PDF document created by PyMuPDF (Fitz).")
            page.insert_text((50, 92), "It contains some sample text for extraction.")
            page.insert_text((50, 112), "Offer: Super Bananas for $0.99/lb")
            doc.save(sample_pdf_path)
            doc.close()
            print(f"Created a sample PDF for testing: {sample_pdf_path}")
        except Exception as e:
            print(f"Could not create sample PDF for testing: {e}")
            sample_pdf_path = None

    if sample_pdf_path and os.path.exists(sample_pdf_path):
        print(f"Attempting to extract text from: {sample_pdf_path}")
        extracted_text = extract_text_from_pdf(sample_pdf_path)

        if extracted_text is not None:
            print("\nExtracted Text:")
            print("--------------------------------------------------")
            print(extracted_text)
            print("--------------------------------------------------")
        else:
            print("\nFailed to extract text from the sample PDF.")
        
        # Clean up the dummy PDF
        # os.remove(sample_pdf_path)
        # print(f"Cleaned up sample PDF: {sample_pdf_path}")
        print(f"Sample PDF '{sample_pdf_path}' remains for inspection. You can delete it manually.")

    else:
        print("Skipping test as sample PDF could not be created or found.")

    print("\nTesting with a non-existent PDF:")
    non_existent_text = extract_text_from_pdf("non_existent_file.pdf")
    if non_existent_text is None:
        print("Correctly handled non-existent PDF (returned None).")
    else:
        print(f"Incorrectly handled non-existent PDF (should have returned None, got: {non_existent_text}).")

```
