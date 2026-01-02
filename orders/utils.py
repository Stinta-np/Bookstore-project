from reportlab.pdfgen import canvas
from django.http import HttpResponse

def generate_invoice(order):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Invoice - Order #{order.id}")

    y = 760
    for item in order.items.all():
        p.drawString(
            100, y,
            f"{item.book.title} x {item.quantity} - ₹{item.price}"
        )
        y -= 20

    p.drawString(100, y-20, f"Total: ₹{order.total_price}")
    p.showPage()
    p.save()

    return response
