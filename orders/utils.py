"""
Utility functions for the orders app.

Helper functions for order processing, calculations, and formatting.
"""

import re
import csv
import math
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta, date

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def generate_order_number() -> str:
    """
    Generate a unique order number.
    
    Format: YYYY########
    Where YYYY is the current year and ######## is a sequential number.
    """
    import time
    import random
    current_year = timezone.now().year
    timestamp = str(int(time.time() * 1000000))  # Include microseconds for uniqueness
    random_part = str(random.randint(10, 99))  # Add random component
    sequential_part = (timestamp + random_part)[-8:]  # Take last 8 digits
    return f"{current_year}{sequential_part}"


def calculate_tax(amount: Decimal, tax_rate: Decimal) -> Decimal:
    """
    Calculate tax amount for a given amount and tax rate.
    
    Args:
        amount: The base amount to calculate tax on
        tax_rate: Tax rate as a percentage (e.g., 8.25 for 8.25%)
    
    Returns:
        Tax amount rounded to 2 decimal places
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    if not isinstance(tax_rate, Decimal):
        tax_rate = Decimal(str(tax_rate))
    
    tax_amount = amount * (tax_rate / Decimal('100'))
    return tax_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def format_currency(amount: Decimal, symbol: str = '$') -> str:
    """
    Format a currency amount with proper formatting.
    
    Args:
        amount: The amount to format
        symbol: Currency symbol to use
    
    Returns:
        Formatted currency string
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # Format with commas for thousands separator
    formatted_amount = f"{amount:,.2f}"
    
    if symbol:
        if amount < 0:
            return f"-{symbol}{formatted_amount[1:]}"  # Handle negative amounts
        return f"{symbol}{formatted_amount}"
    
    return formatted_amount


def validate_postal_code(postal_code: str, country: str) -> bool:
    """
    Validate postal code format for different countries.
    
    Args:
        postal_code: The postal code to validate
        country: Country code (US, CA, GB, etc.)
    
    Returns:
        True if valid, False otherwise
    """
    if not postal_code:
        return False
    
    patterns = {
        'US': r'^\d{5}(-\d{4})?$',  # 12345 or 12345-6789
        'CA': r'^[A-CEGHJ-NPR-TVXY]\d[A-CEGHJ-NPR-TV-Z]\s\d[A-CEGHJ-NPR-TV-Z]\d$',  # K1A 0A6 (exclude D,F,I,O,Q,U,W,Z in first/third pos)
        'GB': r'^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$',  # SW1A 1AA, M1 1AA, etc.
    }
    
    pattern = patterns.get(country.upper())
    if not pattern:
        return True  # Unknown country, assume valid
    
    return bool(re.match(pattern, postal_code.upper()))


def parse_address(address_data: Dict[str, str]) -> str:
    """
    Parse address data into a formatted string.
    
    Args:
        address_data: Dictionary containing address fields
    
    Returns:
        Formatted address string
    """
    parts = []
    
    # Add address parts in order
    if address_data.get('line1'):
        parts.append(address_data['line1'])
    if address_data.get('line2'):
        parts.append(address_data['line2'])
    if address_data.get('city'):
        parts.append(address_data['city'])
    if address_data.get('state') and address_data.get('postal_code'):
        parts.append(f"{address_data['state']} {address_data['postal_code']}")
    elif address_data.get('state'):
        parts.append(address_data['state'])
    elif address_data.get('postal_code'):
        parts.append(address_data['postal_code'])
    if address_data.get('country'):
        parts.append(address_data['country'])
    
    return ', '.join(parts)


def get_shipping_cost(subtotal: Decimal, shipping_method: str) -> Decimal:
    """
    Calculate shipping cost based on subtotal and shipping method.
    
    Args:
        subtotal: Order subtotal
        shipping_method: Shipping method name
    
    Returns:
        Shipping cost
    """
    # Free shipping threshold
    FREE_SHIPPING_THRESHOLD = Decimal('100.00')
    
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return Decimal('0.00')
    
    shipping_rates = {
        'standard': Decimal('5.99'),
        'express': Decimal('12.99'),
        'overnight': Decimal('24.99'),
        'international': Decimal('15.99'),
    }
    
    return shipping_rates.get(shipping_method.lower(), Decimal('5.99'))


def send_order_confirmation_email(order) -> bool:
    """
    Send order confirmation email to customer.
    
    Args:
        order: Order instance
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not order or not order.customer_email:
        return False
    
    try:
        subject = f'Order Confirmation - {order.order_number}'
        # Use simple string templates instead of Django templates for testing
        message = f'Thank you for your order {order.order_number}. Total: ${order.total_amount}'
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'test@example.com'),
            recipient_list=[order.customer_email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def send_order_status_update_email(order, new_status: str) -> bool:
    """
    Send order status update email to customer.
    
    Args:
        order: Order instance
        new_status: New order status
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not order or not order.customer_email:
        return False
    
    try:
        subject = f'Order Update - {order.order_number}'
        # Use simple string templates instead of Django templates for testing
        message = f'Your order {order.order_number} status has been updated to: {new_status}'
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'test@example.com'),
            recipient_list=[order.customer_email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def export_orders_to_csv(orders_queryset) -> str:
    """
    Export orders to CSV format.
    
    Args:
        orders_queryset: QuerySet of orders to export
    
    Returns:
        CSV data as string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Order Number',
        'Customer Email',
        'Status',
        'Total Amount',
        'Created At',
        'Updated At'
    ])
    
    # Write data rows
    for order in orders_queryset:
        writer.writerow([
            order.order_number,
            order.customer_email,
            order.status,
            str(order.total_amount),
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return output.getvalue()


def generate_order_receipt(order, format: str = 'html') -> Union[str, bytes]:
    """
    Generate order receipt in specified format.
    
    Args:
        order: Order instance
        format: Output format ('html', 'text', 'pdf')
    
    Returns:
        Receipt content in specified format
    
    Raises:
        ValueError: If order is None or format is invalid
    """
    if not order:
        raise ValueError("Order cannot be None")
    
    if format not in ['html', 'text', 'pdf']:
        raise ValueError("Format must be 'html', 'text', or 'pdf'")
    
    # Generate receipt content with order items
    items_text = ""
    if hasattr(order, 'items') and order.items.exists():
        items_text = "\n    Items:"
        for item in order.items.all():
            items_text += f"\n    - {item.product.name} x {item.quantity} @ ${item.unit_price}"
    
    receipt_content = f"""
    Order Receipt
    Order Number: {order.order_number}
    Customer: {order.customer_email}
    Total: ${order.total_amount}
    Status: {order.status}{items_text}
    """
    
    if format == 'html':
        return f"<html><body><pre>{receipt_content}</pre></body></html>"
    elif format == 'text':
        return receipt_content
    elif format == 'pdf':
        # Mock PDF content - in real implementation, use proper PDF library
        pdf_header = b'%PDF-1.4\n'
        pdf_content = receipt_content.encode('utf-8')
        return pdf_header + pdf_content
    
    # This should never be reached, but added for completeness
    return receipt_content


# Additional utility functions for completeness

def slugify_string(text: str) -> str:
    """
    Convert a string to a slug format.
    
    Args:
        text: String to slugify
    
    Returns:
        Slugified string
    """
    import re
    from django.utils.text import slugify
    return slugify(text)


def format_phone_number(phone: str) -> str:
    """
    Format phone number for display.
    
    Args:
        phone: Phone number string
    
    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if format is unexpected


def mask_credit_card(card_number: str) -> str:
    """
    Mask credit card number for security.
    
    Args:
        card_number: Credit card number
    
    Returns:
        Masked credit card number
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', card_number)
    
    if len(digits) < 4:
        return card_number  # Return original if too short
    
    if len(digits) == 16:
        return f"****-****-****-{digits[-4:]}"
    elif len(digits) == 15:
        return f"****-****-***-{digits[-4:]}"
    else:
        return card_number  # Return original if unexpected format


def calculate_distance(coord1: tuple, coord2: tuple) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        coord1: Tuple of (latitude, longitude) for first point
        coord2: Tuple of (latitude, longitude) for second point
    
    Returns:
        Distance in miles
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in miles
    r = 3956
    
    return c * r


def calculate_business_days(start_date: date, business_days: int) -> date:
    """
    Calculate a date that is a specified number of business days from start date.
    
    Args:
        start_date: Starting date
        business_days: Number of business days to add
    
    Returns:
        End date after adding business days
    """
    current_date = start_date
    days_added = 0
    
    while days_added < business_days:
        current_date += timedelta(days=1)
        # Monday = 0, Sunday = 6
        if current_date.weekday() < 5:  # Monday through Friday
            days_added += 1
    
    return current_date