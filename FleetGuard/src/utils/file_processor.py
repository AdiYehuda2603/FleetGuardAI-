"""
File Processor - Upload Handler
Processes uploaded PDF and CSV files and converts to database format
"""

import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime
import os


class FileProcessor:
    """
    Handles file uploads (PDF/CSV) and converts them to FleetGuard database format
    """

    def __init__(self):
        self.supported_formats = ['.pdf', '.csv']

    def process_uploaded_file(self, file_obj, file_type):
        """
        Main entry point for processing uploaded files

        Args:
            file_obj: Streamlit UploadedFile object or file-like object
            file_type: File type ('application/pdf' or 'text/csv')

        Returns:
            pandas DataFrame in FleetGuard format (invoices schema)
        """
        if 'pdf' in file_type.lower():
            return self._process_pdf(file_obj)
        elif 'csv' in file_type.lower():
            return self._process_csv(file_obj)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _process_pdf(self, pdf_file):
        """
        Extract invoice data from PDF file

        Args:
            pdf_file: PDF file object

        Returns:
            pandas DataFrame with invoice data
        """
        try:
            # Read PDF content
            pdf_bytes = pdf_file.read() if hasattr(pdf_file, 'read') else pdf_file

            # Parse PDF with pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                # Extract text from all pages
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"

            # Parse invoice data from text
            invoice_data = self._parse_invoice_text(full_text)

            # Convert to DataFrame
            df = pd.DataFrame([invoice_data])

            return df

        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")

    def _parse_invoice_text(self, text):
        """
        Parse invoice data from extracted PDF text

        Args:
            text: Extracted text from PDF

        Returns:
            dict: Invoice data in database format
        """
        invoice_data = {}

        # Extract invoice number (pattern: חשבונית מס' XXXXX or Invoice No. XXXXX)
        invoice_match = re.search(r'(?:חשבונית מס\'|Invoice No\.|מס\')\s*:?\s*(\S+)', text)
        if invoice_match:
            invoice_data['invoice_no'] = invoice_match.group(1)
        else:
            # Generate temporary invoice number
            invoice_data['invoice_no'] = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Extract date (pattern: תאריך: DD/MM/YYYY or Date: YYYY-MM-DD)
        date_match = re.search(r'(?:תאריך|Date)\s*:?\s*(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})', text)
        if date_match:
            date_str = date_match.group(1)
            # Convert to YYYY-MM-DD format
            if '/' in date_str or '-' in date_str:
                try:
                    parsed_date = pd.to_datetime(date_str, dayfirst=True)
                    invoice_data['date'] = parsed_date.strftime('%Y-%m-%d')
                except:
                    invoice_data['date'] = datetime.now().strftime('%Y-%m-%d')
        else:
            invoice_data['date'] = datetime.now().strftime('%Y-%m-%d')

        # Extract workshop name
        workshop_match = re.search(r'(?:מוסך|Workshop|גראז\')\s*:?\s*([^\n]+)', text)
        if workshop_match:
            invoice_data['workshop'] = workshop_match.group(1).strip()
        else:
            invoice_data['workshop'] = "Unknown Workshop"

        # Extract vehicle ID (pattern: VH-XX or רכב: VH-XX)
        vehicle_match = re.search(r'(?:רכב|Vehicle)\s*:?\s*(VH-\d+)', text)
        if vehicle_match:
            invoice_data['vehicle_id'] = vehicle_match.group(1)
        else:
            # Try to find any VH-XX pattern
            vh_match = re.search(r'VH-\d+', text)
            if vh_match:
                invoice_data['vehicle_id'] = vh_match.group(0)
            else:
                invoice_data['vehicle_id'] = None  # Will fail validation

        # Extract plate number
        plate_match = re.search(r'(?:מספר רישוי|Plate|לוחית)\s*:?\s*(\d{2,3}-\d{2,3}-\d{2,3})', text)
        if plate_match:
            invoice_data['plate'] = plate_match.group(1)
        else:
            invoice_data['plate'] = None

        # Extract make/model
        model_match = re.search(r'(?:דגם|Model)\s*:?\s*([^\n]+)', text)
        if model_match:
            invoice_data['make_model'] = model_match.group(1).strip()
        else:
            invoice_data['make_model'] = None

        # Extract odometer reading (pattern: קילומטרז': XXXXX or Odometer: XXXXX)
        odo_match = re.search(r'(?:קילומטרז\'|Odometer|ק\"מ)\s*:?\s*([\d,]+)', text)
        if odo_match:
            odo_str = odo_match.group(1).replace(',', '')
            try:
                invoice_data['odometer_km'] = int(odo_str)
            except ValueError:
                invoice_data['odometer_km'] = None
        else:
            invoice_data['odometer_km'] = None  # Will fail validation

        # Extract totals
        # Pattern for subtotal
        subtotal_match = re.search(r'(?:סכום ביניים|Subtotal)\s*:?\s*([\d,\.]+)', text)
        if subtotal_match:
            invoice_data['subtotal'] = float(subtotal_match.group(1).replace(',', ''))
        else:
            invoice_data['subtotal'] = 0.0

        # Pattern for VAT
        vat_match = re.search(r'(?:מע\"מ|VAT)\s*:?\s*([\d,\.]+)', text)
        if vat_match:
            invoice_data['vat'] = float(vat_match.group(1).replace(',', ''))
        else:
            invoice_data['vat'] = 0.0

        # Pattern for total (סה"כ or Total)
        total_match = re.search(r'(?:סה\"כ|Total|לתשלום)\s*:?\s*₪?\s*([\d,\.]+)', text)
        if total_match:
            invoice_data['total'] = float(total_match.group(1).replace(',', ''))
        else:
            # Calculate from subtotal + VAT if available
            if invoice_data['subtotal'] > 0:
                invoice_data['total'] = invoice_data['subtotal'] + invoice_data['vat']
            else:
                invoice_data['total'] = None  # Will fail validation

        # Extract kind (routine/tires/lights/spark_plugs) - infer from content
        text_lower = text.lower()
        if 'tire' in text_lower or 'צמיג' in text_lower:
            invoice_data['kind'] = 'tires'
        elif 'light' in text_lower or 'פנס' in text_lower or 'נורה' in text_lower:
            invoice_data['kind'] = 'lights'
        elif 'spark' in text_lower or 'מצת' in text_lower:
            invoice_data['kind'] = 'spark_plugs'
        else:
            invoice_data['kind'] = 'routine'

        # PDF file reference
        invoice_data['pdf_file'] = None  # Can be set later if needed

        return invoice_data

    def _process_csv(self, csv_file):
        """
        Parse CSV file with invoice data

        Args:
            csv_file: CSV file object

        Returns:
            pandas DataFrame with invoice data
        """
        try:
            # Read CSV
            df = pd.read_csv(csv_file)

            # Validate required columns exist
            required_cols = ['vehicle_id', 'date', 'odometer_km', 'workshop', 'total']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                raise ValueError(f"CSV missing required columns: {', '.join(missing_cols)}")

            # Ensure correct data types
            if 'odometer_km' in df.columns:
                df['odometer_km'] = pd.to_numeric(df['odometer_km'], errors='coerce')

            if 'total' in df.columns:
                df['total'] = pd.to_numeric(df['total'], errors='coerce')

            if 'subtotal' in df.columns:
                df['subtotal'] = pd.to_numeric(df['subtotal'], errors='coerce')
            else:
                df['subtotal'] = 0.0

            if 'vat' in df.columns:
                df['vat'] = pd.to_numeric(df['vat'], errors='coerce')
            else:
                df['vat'] = 0.0

            # Ensure date is in correct format
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')

            # Add missing optional columns with defaults
            if 'kind' not in df.columns:
                df['kind'] = 'routine'

            if 'invoice_no' not in df.columns:
                # Generate invoice numbers
                df['invoice_no'] = [f"CSV-{i:05d}" for i in range(len(df))]

            if 'pdf_file' not in df.columns:
                df['pdf_file'] = None

            return df

        except Exception as e:
            raise ValueError(f"Error processing CSV: {str(e)}")

    def save_to_uploads(self, file_obj, filename=None):
        """
        Save uploaded file to data/uploads directory

        Args:
            file_obj: File object to save
            filename: Custom filename (auto-generates if None)

        Returns:
            str: Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"upload_{timestamp}"

        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        uploads_dir = os.path.join(base_dir, "data", "uploads")

        # Ensure directory exists
        os.makedirs(uploads_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(uploads_dir, filename)

        with open(file_path, 'wb') as f:
            content = file_obj.read() if hasattr(file_obj, 'read') else file_obj
            f.write(content)

        return file_path


# --- Testing ---
if __name__ == "__main__":
    # Test CSV processing
    test_csv_data = """vehicle_id,date,odometer_km,workshop,total,subtotal,vat,kind
VH-01,2024-01-15,50000,Yossi Garage,1500.00,1260.50,239.50,routine
VH-02,2024-01-16,75000,Yoav Garage,2000.00,1680.67,319.33,tires"""

    processor = FileProcessor()

    # Test with CSV string
    csv_io = io.StringIO(test_csv_data)
    df = processor._process_csv(csv_io)

    print("\n" + "=" * 80)
    print("FILE PROCESSOR TEST - CSV")
    print("=" * 80)
    print(f"\nProcessed {len(df)} rows:")
    print(df.to_string())
    print("\n" + "=" * 80)
