"""Generate samples/excel/sales_book.xlsx. All data is fictional. Run with the project virtual environment."""
from pathlib import Path

from openpyxl import Workbook


def main() -> Path:
    book = Workbook()
    sheet = book.active
    sheet.title = "customers"
    sheet.append(["customer_code", "name", "email", "credit_limit", "joined_on"])
    for row in [("C-01", "Lark Sample Co", "lark@example.com", 500.5, "2024-01-05"),
                ("C-02", "Finch Demo Ltd", "finch@example.org", 1200, "2024-02-11"),
                ("C-03", "Robin Test LLC", "robin@example.net", 300, "2024-03-19"),
                ("C-03", "Robin Test LLC", "robin@example.net", 300, "2024-03-19")]:
        sheet.append(row)
    orders = book.create_sheet("orders")
    orders.append(["order_ref", "customer_code", "amount", "status"])
    for row in [("O-1", "C-01", 45.5, "open"), ("O-2", "C-02", 12, "open"), ("O-3", "C-99", 7.25, "cancelled")]:
        orders.append(row)
    target = Path(__file__).parent / "excel" / "sales_book.xlsx"
    target.parent.mkdir(exist_ok=True)
    book.save(target)
    return target


if __name__ == "__main__":
    print(main())
