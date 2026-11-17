"""Generate policy documents in data/docs/ from ShopEasy ground-truth facts.

Ground-truth facts from Section 6 of AGENTS.md are strictly followed.
No new numbers, prices, cities, or promises are added.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings

DOCS_DIR = backend_dir / "data" / "docs"

DOCUMENTS = {
    "returns_and_refunds.md": """# ShopEasy Returns and Refunds Policy

## Return Window and Eligibility
- Customers may request a return within 30 days of delivery.
- The original receipt is strictly required for all returns.
- Items must be unused and in their original packaging.

## Non-Returnable Items
- The following items cannot be returned under any circumstances:
  - Opened software
  - Earbuds
  - Gift cards

## Return Pickup Fees
- **Premium Members:** Free return pickup on all eligible items.
- **Standard Customers:** Return pickup fee is 99 rupees.

## Refund Processing
- Refunds are issued to the original payment method.
- The refund will be credited within 5 to 7 business days after the returned item is received and inspected at our warehouse.
""",
    "damaged_or_wrong_items.md": """# ShopEasy Damaged or Wrong Items Policy

## Reporting Window
- If an item arrives damaged or if you receive the wrong product, you must report it within 48 hours of delivery.

## How to Report
- Send an email to support@shopeasy.example.
- You must attach 2 clear photos showing the item and its packaging.

## Resolution
- Once your report is approved by our support team, a free replacement will be dispatched within 3 business days.
""",
    "shipping_and_delivery.md": """# ShopEasy Shipping and Delivery Policy

## Shipping Coverage
- ShopEasy ships exclusively within India.
- We do not ship to any addresses outside India.

## Standard Delivery
- Delivery time: 3 to 5 business days across India.
- Free shipping on all orders above 999 rupees.
- For orders of 999 rupees or less, the standard delivery fee is 49 rupees.

## Express Delivery
- Delivery time: 1 to 2 business days.
- Express delivery costs an additional 150 rupees.
- **Available Cities Only:** Express delivery is available strictly in the following 5 cities:
  - Hyderabad
  - Bengaluru
  - Chennai
  - Mumbai
  - Delhi
- Express delivery is not available in any other cities.

## Order Tracking
- A tracking link is automatically emailed to the customer once the order ships.
""",
    "order_cancellations.md": """# ShopEasy Order Cancellation Policy

## Cancellation Eligibility
- An order can be cancelled only while its status is `processing`.
- Once an order status changes to `shipped`, it cannot be cancelled.
- If your order has already shipped, you may refuse delivery at your doorstep or initiate a return after delivery (subject to return guidelines).

## Refund for Cancelled Orders
- Cancelled orders are refunded to the original payment method within 3 to 5 business days.
""",
    "payments_and_errors.md": """# ShopEasy Payments and Error Resolution

## Accepted Payment Methods
- UPI
- Credit cards
- Debit cards
- Net banking

## Cash on Delivery (COD)
- Cash on delivery is available for orders up to 5000 rupees. Orders exceeding 5000 rupees must be paid online.

## Equated Monthly Installments (EMI)
- EMI options are available on orders above 10000 rupees with selected partner banks.

## Payment Error Codes and Troubleshooting
- **Error P-1042:** Payment gateway timed out. Please wait 10 minutes and retry the transaction.
- **Error P-2210:** Card was declined by your bank. Please contact your card-issuing bank or use another payment method.
""",
    "warranty_and_protection.md": """# ShopEasy Warranty and Device Protection

## Manufacturer Warranty
- All electronics sold on ShopEasy include a 1-year manufacturer warranty starting from the date of delivery.
- **What is NOT covered:**
  - Water damage
  - Physical damage caused by the customer

## Extended Warranty for Laptops
- Customers who purchase a laptop can buy a 2-year extended warranty for 2999 rupees.
- The extended warranty must be purchased within 30 days of the original laptop purchase date.
""",
    "premium_membership.md": """# ShopEasy Premium Membership

## Membership Pricing
- ShopEasy Premium membership costs 499 rupees per year.

## Member Benefits
- Free express delivery on eligible orders in supported cities.
- Free return pickup (saves the 99 rupees standard return fee).
- Early access to sales and promotions.

## Cancellation and Refunds
- Members may cancel their membership within 7 days of enrollment for a full refund.
- After 7 days, the membership fee is strictly non-refundable.
""",
    "customer_support_and_account.md": """# ShopEasy Customer Support and Account Management

## Support Hours and Contact
- **Hours:** Monday to Saturday, 9:00 AM to 7:00 PM IST.
- **Closures:** Closed on Sundays and Indian national holidays.
- **Email:** support@shopeasy.example
- Support inquiries receive a reply within 24 hours.

## Password Reset
- Click "Forgot password" on the login page.
- The password reset link sent to your email expires after 30 minutes.

## Account Deletion
- To delete your ShopEasy account, send an email request to privacy@shopeasy.example.
- Account deletion requests are completed within 14 days.
""",
}


def generate_documents() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating policy documents in: {DOCS_DIR}")
    for filename, content in DOCUMENTS.items():
        filepath = DOCS_DIR / filename
        filepath.write_text(content.strip() + "\n", encoding="utf-8")
        word_count = len(content.split())
        print(f"  - Created {filename} ({word_count} words)")

    print(f"\nSuccessfully generated {len(DOCUMENTS)} policy documents.")


if __name__ == "__main__":
    generate_documents()
