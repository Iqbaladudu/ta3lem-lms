from django.dispatch import Signal

# Fired when a payment is completed successfully
# sender: Order instance
# provides: order, user
payment_completed = Signal()

# Fired when a payment fails or is rejected
# sender: Order instance
# provides: order, reason
payment_failed = Signal()

# Import email handlers to register them
from . import emails  # noqa
