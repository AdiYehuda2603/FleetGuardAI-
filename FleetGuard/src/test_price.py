from src.extractor import InvoiceExtractor
import glob
import os

# מוצאים קובץ אחד לבדיקה
files = glob.glob("data/raw_invoices/*.pdf")

if files:
    # לוקחים את הקובץ הראשון
    test_file = files[0]
    print(f"📄 בודק את הקובץ: {os.path.basename(test_file)}")
    
    # מפעילים את ה-Extractor החדש
    extractor = InvoiceExtractor(test_file)
    data = extractor.extract()
    
    print("-" * 30)
    print(f"💰 הסכום שנמצא: {data['total_amount']}")
    print("-" * 30)
    
    # בדיקה האם הצלחנו
    if data['total_amount'] > 0:
        print("✅ הצלחה! הקוד עובד. עכשיו צריך להריץ את main.py כדי לעדכן את כולם.")
    else:
        print("❌ כישלון. הסכום עדיין 0. הבעיה היא בקוד החילוץ.")
        # הדפסת עזרה לדיבוג - מה הטבלה שהמחשב רואה?
        import pdfplumber
        with pdfplumber.open(test_file) as pdf:
            print("הצצה לטבלה הגולמית שהמחשב רואה:")
            for row in pdf.pages[0].extract_tables()[0]:
                print(row)
else:
    print("לא נמצאו קבצים בתיקייה!")