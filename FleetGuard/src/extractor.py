import pdfplumber
import re
import os

class InvoiceExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.text = ""
        self.data = {
            "filename": os.path.basename(pdf_path),
            "invoice_num": None,
            "date": None,
            "garage_name": "General Garage",
            "vehicle_id": None,
            "total_amount": 0.0,
            "items": []
        }

    def extract(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[0]
            self.text = page.extract_text() or ""
            self._extract_metadata_regex()
            self._extract_tables_logic(page)
            self._extract_garage_hebrew()
        return self.data

    def _extract_metadata_regex(self):
        # חילוץ מספרי חשבונית, תאריך ורכב (כמו קודם)
        inv_match = re.search(r"(INV-\d+)", self.text)
        if inv_match: self.data["invoice_num"] = inv_match.group(1)

        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", self.text)
        if date_match: self.data["date"] = date_match.group(1)

        veh_match = re.search(r"(VH-\d+)", self.text)
        if veh_match: self.data["vehicle_id"] = veh_match.group(1)

    def _extract_tables_logic(self, page):
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                # ניקוי: מחיקת גרשיים כפולים ורווחים מיותרים
                clean_row = [str(cell).replace('"', '').strip() if cell else "" for cell in row]
                row_text = " ".join(clean_row)
                
                # --- תיקון זיהוי סה"כ ---
                # מחפשים מילות מפתח גם בעברית רגילה וגם בהפוכה
                keywords = ['סה"כ', 'סהכ', 'כ"הס', 'כהס', 'לתשלום', 'םולשתל']
                
                if any(word in row_text for word in keywords):
                    # מחפשים את המספר העשרוני האחרון בשורה (המחיר הסופי)
                    prices = re.findall(r"(\d+\.\d+)", row_text)
                    if prices:
                        self.data["total_amount"] = float(prices[-1])
                    continue

                # --- זיהוי פריטים ---
                if len(clean_row) >= 3 and self._has_numbers(row_text) and "תיאור" not in row_text:
                    try:
                        nums = re.findall(r"([\d\.]+)", row_text)
                        if len(nums) >= 2:
                            price = float(nums[-1])
                            qty = int(float(nums[-2]))
                            desc = re.sub(r"[\d\.\,]+", "", row_text).replace('סה"כ', '').strip()
                            
                            # הופך עברית אם צריך
                            if self._is_hebrew(desc):
                                desc = desc[::-1]
                                
                            item = {
                                "description": desc,
                                "category": "General",
                                "qty": qty,
                                "price": price
                            }
                            self.data["items"].append(item)
                    except:
                        pass

    def _extract_garage_hebrew(self):
        if "ךסומ" in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if "ךסומ" in line:
                    clean_name = line.replace("(הקידב)", "").strip()[::-1]
                    self.data["garage_name"] = clean_name
                    break

    def _has_numbers(self, text):
        return bool(re.search(r"\d", text))

    def _is_hebrew(self, text):
        return any("\u0590" <= c <= "\u05EA" for c in text)