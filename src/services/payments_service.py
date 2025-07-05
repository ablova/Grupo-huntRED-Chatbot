"""
HuntRED® v2 - Payments & Billing Service
Complete payment processing and billing management system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum
import hashlib
import hmac

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    OXXO = "oxxo"
    SPEI = "spei"

class BillingCycle(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentsService:
    """Complete payments and billing management"""
    
    def __init__(self, db):
        self.db = db
        
        # Payment processors configuration
        self.payment_processors = {
            "stripe": {
                "name": "Stripe",
                "supported_methods": ["credit_card", "bank_transfer"],
                "fees": {"credit_card": 0.029, "bank_transfer": 0.008},
                "currencies": ["MXN", "USD"],
                "webhook_endpoint": "/webhooks/stripe"
            },
            "paypal": {
                "name": "PayPal",
                "supported_methods": ["paypal"],
                "fees": {"paypal": 0.035},
                "currencies": ["MXN", "USD"],
                "webhook_endpoint": "/webhooks/paypal"
            },
            "conekta": {
                "name": "Conekta",
                "supported_methods": ["credit_card", "oxxo", "spei"],
                "fees": {"credit_card": 0.036, "oxxo": 12.00, "spei": 3.00},
                "currencies": ["MXN"],
                "webhook_endpoint": "/webhooks/conekta"
            }
        }
        
        # Tax rates by country/region
        self.tax_rates = {
            "MX": {
                "IVA": 0.16,
                "ISR": 0.125,  # For services
                "regions": {
                    "frontera": {"IVA": 0.08}  # Border region
                }
            },
            "US": {
                "sales_tax": 0.08  # Average
            }
        }
    
    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new payment"""
        try:
            payment_id = str(uuid.uuid4())
            
            # Extract payment information
            amount = Decimal(str(payment_data["amount"]))
            currency = payment_data.get("currency", "MXN")
            method = PaymentMethod(payment_data["payment_method"])
            customer_info = payment_data.get("customer_info", {})
            
            # Calculate fees and taxes
            fees = self._calculate_fees(amount, method, currency)
            taxes = self._calculate_taxes(amount, customer_info.get("country", "MX"))
            
            # Create payment record
            payment = {
                "id": payment_id,
                "amount": amount,
                "currency": currency,
                "method": method.value,
                "status": PaymentStatus.PENDING.value,
                "customer_info": customer_info,
                "fees": fees,
                "taxes": taxes,
                "total_amount": amount + fees["total"] + taxes["total"],
                "created_at": datetime.now(),
                "metadata": {
                    "invoice_id": payment_data.get("invoice_id"),
                    "subscription_id": payment_data.get("subscription_id"),
                    "description": payment_data.get("description"),
                    "reference": payment_data.get("reference")
                }
            }
            
            # Process payment based on method
            if method == PaymentMethod.CREDIT_CARD:
                result = await self._process_credit_card_payment(payment, payment_data)
            elif method == PaymentMethod.BANK_TRANSFER:
                result = await self._process_bank_transfer(payment, payment_data)
            elif method == PaymentMethod.OXXO:
                result = await self._process_oxxo_payment(payment, payment_data)
            elif method == PaymentMethod.SPEI:
                result = await self._process_spei_payment(payment, payment_data)
            else:
                result = {"success": False, "error": "Payment method not supported"}
            
            if result["success"]:
                payment["status"] = PaymentStatus.PROCESSING.value
                payment["processor_response"] = result
                
                # Save to database
                # await self._save_payment(payment)
                
                logger.info(f"Payment {payment_id} created successfully")
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "payment": payment,
                    "processor_response": result
                }
            else:
                payment["status"] = PaymentStatus.FAILED.value
                payment["error"] = result.get("error")
                
                return {
                    "success": False,
                    "payment_id": payment_id,
                    "error": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_fees(self, amount: Decimal, method: PaymentMethod, currency: str) -> Dict[str, Any]:
        """Calculate processing fees"""
        
        fees = {
            "processor_fee": Decimal("0.00"),
            "platform_fee": Decimal("0.00"),
            "total": Decimal("0.00")
        }
        
        # Processor fees
        if method == PaymentMethod.CREDIT_CARD:
            fees["processor_fee"] = amount * Decimal("0.029")  # 2.9%
        elif method == PaymentMethod.BANK_TRANSFER:
            fees["processor_fee"] = amount * Decimal("0.008")  # 0.8%
        elif method == PaymentMethod.OXXO:
            fees["processor_fee"] = Decimal("12.00")  # Fixed fee
        elif method == PaymentMethod.SPEI:
            fees["processor_fee"] = Decimal("3.00")  # Fixed fee
        
        # Platform fee (our margin)
        fees["platform_fee"] = amount * Decimal("0.005")  # 0.5%
        
        fees["total"] = fees["processor_fee"] + fees["platform_fee"]
        
        return fees
    
    def _calculate_taxes(self, amount: Decimal, country: str) -> Dict[str, Any]:
        """Calculate taxes based on location"""
        
        taxes = {
            "iva": Decimal("0.00"),
            "isr": Decimal("0.00"),
            "total": Decimal("0.00")
        }
        
        if country == "MX":
            # IVA (16% in Mexico)
            taxes["iva"] = amount * Decimal("0.16")
            # ISR for services (12.5%)
            taxes["isr"] = amount * Decimal("0.125")
        elif country == "US":
            # Sales tax (varies by state, using average)
            taxes["sales_tax"] = amount * Decimal("0.08")
        
        taxes["total"] = sum(taxes.values())
        
        return taxes
    
    async def _process_credit_card_payment(self, payment: Dict[str, Any], 
                                         payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process credit card payment"""
        try:
            # Mock Stripe integration
            card_info = payment_data.get("card_info", {})
            
            # Validate card information
            if not self._validate_card_info(card_info):
                return {"success": False, "error": "Invalid card information"}
            
            # Create payment intent (mock)
            payment_intent = {
                "id": f"pi_{uuid.uuid4().hex[:24]}",
                "amount": int(payment["total_amount"] * 100),  # Amount in cents
                "currency": payment["currency"].lower(),
                "status": "requires_confirmation",
                "client_secret": f"pi_{uuid.uuid4().hex[:24]}_secret_{uuid.uuid4().hex[:16]}"
            }
            
            return {
                "success": True,
                "payment_intent": payment_intent,
                "requires_action": False,
                "next_action": None
            }
            
        except Exception as e:
            logger.error(f"Error processing credit card payment: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_bank_transfer(self, payment: Dict[str, Any], 
                                   payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process bank transfer payment"""
        try:
            # Generate bank transfer instructions
            transfer_instructions = {
                "bank_name": "BBVA México",
                "account_number": "0123456789",
                "clabe": "012345678901234567",
                "beneficiary": "HuntRED México S.A. de C.V.",
                "reference": f"HR-{payment['id'][:8].upper()}",
                "amount": float(payment["total_amount"]),
                "currency": payment["currency"],
                "expiration_date": (datetime.now() + timedelta(days=3)).isoformat()
            }
            
            return {
                "success": True,
                "transfer_instructions": transfer_instructions,
                "requires_manual_verification": True
            }
            
        except Exception as e:
            logger.error(f"Error processing bank transfer: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_oxxo_payment(self, payment: Dict[str, Any], 
                                  payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process OXXO payment"""
        try:
            # Generate OXXO payment reference
            oxxo_reference = f"OXXO{uuid.uuid4().hex[:12].upper()}"
            
            oxxo_instructions = {
                "reference": oxxo_reference,
                "amount": float(payment["total_amount"]),
                "currency": "MXN",
                "barcode": self._generate_barcode(oxxo_reference),
                "expiration_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "instructions": [
                    "Acude a cualquier tienda OXXO",
                    "Proporciona el código de referencia al cajero",
                    "Realiza el pago en efectivo",
                    "Conserva tu comprobante de pago"
                ]
            }
            
            return {
                "success": True,
                "oxxo_instructions": oxxo_instructions,
                "requires_manual_verification": True
            }
            
        except Exception as e:
            logger.error(f"Error processing OXXO payment: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_spei_payment(self, payment: Dict[str, Any], 
                                  payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process SPEI payment"""
        try:
            # Generate SPEI transfer instructions
            spei_instructions = {
                "clabe": "012345678901234567",
                "beneficiary": "HuntRED México S.A. de C.V.",
                "amount": float(payment["total_amount"]),
                "currency": "MXN",
                "reference": f"SPEI-{payment['id'][:8].upper()}",
                "bank_name": "BBVA México",
                "expiration_date": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            return {
                "success": True,
                "spei_instructions": spei_instructions,
                "requires_manual_verification": True
            }
            
        except Exception as e:
            logger.error(f"Error processing SPEI payment: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_card_info(self, card_info: Dict[str, Any]) -> bool:
        """Validate credit card information"""
        required_fields = ["number", "exp_month", "exp_year", "cvc"]
        
        for field in required_fields:
            if field not in card_info or not card_info[field]:
                return False
        
        # Basic card number validation (Luhn algorithm)
        card_number = card_info["number"].replace(" ", "").replace("-", "")
        if not self._luhn_check(card_number):
            return False
        
        # Expiration date validation
        exp_month = int(card_info["exp_month"])
        exp_year = int(card_info["exp_year"])
        
        if exp_month < 1 or exp_month > 12:
            return False
        
        current_year = datetime.now().year
        if exp_year < current_year or exp_year > current_year + 20:
            return False
        
        return True
    
    def _luhn_check(self, card_number: str) -> bool:
        """Validate card number using Luhn algorithm"""
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        return luhn_checksum(card_number) == 0
    
    def _generate_barcode(self, reference: str) -> str:
        """Generate barcode for OXXO payment"""
        # Mock barcode generation
        return f"||{reference}||{datetime.now().strftime('%Y%m%d')}||"
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice"""
        try:
            invoice_id = str(uuid.uuid4())
            
            # Extract invoice information
            customer_info = invoice_data["customer_info"]
            line_items = invoice_data["line_items"]
            
            # Calculate totals
            subtotal = sum(Decimal(str(item["amount"])) for item in line_items)
            taxes = self._calculate_taxes(subtotal, customer_info.get("country", "MX"))
            total = subtotal + taxes["total"]
            
            # Create invoice
            invoice = {
                "id": invoice_id,
                "invoice_number": self._generate_invoice_number(),
                "customer_info": customer_info,
                "line_items": line_items,
                "subtotal": subtotal,
                "taxes": taxes,
                "total": total,
                "currency": invoice_data.get("currency", "MXN"),
                "status": InvoiceStatus.DRAFT.value,
                "created_at": datetime.now(),
                "due_date": datetime.now() + timedelta(days=30),
                "metadata": {
                    "subscription_id": invoice_data.get("subscription_id"),
                    "billing_period": invoice_data.get("billing_period"),
                    "notes": invoice_data.get("notes")
                }
            }
            
            # Save to database
            # await self._save_invoice(invoice)
            
            logger.info(f"Invoice {invoice_id} created successfully")
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "invoice": invoice
            }
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"INV-{timestamp}-{random_suffix}"
    
    async def process_subscription_billing(self, subscription_id: str) -> Dict[str, Any]:
        """Process subscription billing"""
        try:
            # Get subscription details (mock)
            subscription = await self._get_subscription(subscription_id)
            
            if not subscription:
                return {"success": False, "error": "Subscription not found"}
            
            # Check if billing is due
            if not self._is_billing_due(subscription):
                return {"success": False, "error": "Billing not due yet"}
            
            # Create invoice for subscription
            invoice_data = {
                "customer_info": subscription["customer_info"],
                "line_items": [
                    {
                        "description": f"Subscription - {subscription['plan_name']}",
                        "amount": subscription["amount"],
                        "quantity": 1
                    }
                ],
                "subscription_id": subscription_id,
                "billing_period": subscription["current_period"]
            }
            
            invoice_result = await self.create_invoice(invoice_data)
            
            if invoice_result["success"]:
                # Attempt to charge customer
                payment_data = {
                    "amount": invoice_result["invoice"]["total"],
                    "currency": subscription["currency"],
                    "payment_method": subscription["payment_method"],
                    "customer_info": subscription["customer_info"],
                    "invoice_id": invoice_result["invoice_id"]
                }
                
                payment_result = await self.create_payment(payment_data)
                
                return {
                    "success": True,
                    "invoice": invoice_result["invoice"],
                    "payment": payment_result
                }
            else:
                return invoice_result
                
        except Exception as e:
            logger.error(f"Error processing subscription billing: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details"""
        # Mock subscription data
        return {
            "id": subscription_id,
            "customer_info": {
                "name": "Test Customer",
                "email": "test@example.com",
                "country": "MX"
            },
            "plan_name": "Professional Plan",
            "amount": Decimal("7500.00"),
            "currency": "MXN",
            "payment_method": "credit_card",
            "billing_cycle": "monthly",
            "current_period": {
                "start": datetime.now().replace(day=1),
                "end": datetime.now().replace(day=28)
            },
            "next_billing_date": datetime.now() + timedelta(days=30)
        }
    
    def _is_billing_due(self, subscription: Dict[str, Any]) -> bool:
        """Check if subscription billing is due"""
        next_billing_date = subscription["next_billing_date"]
        return datetime.now() >= next_billing_date
    
    async def handle_webhook(self, provider: str, payload: Dict[str, Any], 
                           signature: str) -> Dict[str, Any]:
        """Handle payment processor webhooks"""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(provider, payload, signature):
                return {"success": False, "error": "Invalid signature"}
            
            event_type = payload.get("type") or payload.get("event_type")
            
            if provider == "stripe":
                return await self._handle_stripe_webhook(event_type, payload)
            elif provider == "conekta":
                return await self._handle_conekta_webhook(event_type, payload)
            elif provider == "paypal":
                return await self._handle_paypal_webhook(event_type, payload)
            else:
                return {"success": False, "error": "Unknown provider"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"success": False, "error": str(e)}
    
    def _verify_webhook_signature(self, provider: str, payload: Dict[str, Any], 
                                signature: str) -> bool:
        """Verify webhook signature"""
        # Mock signature verification
        # In real implementation, verify using provider's secret key
        return True
    
    async def _handle_stripe_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        if event_type == "payment_intent.succeeded":
            payment_intent = payload["data"]["object"]
            # Update payment status to completed
            await self._update_payment_status(payment_intent["id"], PaymentStatus.COMPLETED)
            
        elif event_type == "payment_intent.payment_failed":
            payment_intent = payload["data"]["object"]
            # Update payment status to failed
            await self._update_payment_status(payment_intent["id"], PaymentStatus.FAILED)
        
        return {"success": True, "processed": True}
    
    async def _handle_conekta_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Conekta webhook events"""
        if event_type == "order.paid":
            order = payload["data"]["object"]
            # Update payment status to completed
            await self._update_payment_status(order["id"], PaymentStatus.COMPLETED)
            
        return {"success": True, "processed": True}
    
    async def _handle_paypal_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PayPal webhook events"""
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            payment = payload["resource"]
            # Update payment status to completed
            await self._update_payment_status(payment["id"], PaymentStatus.COMPLETED)
            
        return {"success": True, "processed": True}
    
    async def _update_payment_status(self, payment_id: str, status: PaymentStatus) -> None:
        """Update payment status"""
        # Mock implementation
        logger.info(f"Payment {payment_id} status updated to {status.value}")
    
    async def generate_financial_report(self, report_type: str, 
                                      date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial reports"""
        try:
            start_date = datetime.fromisoformat(date_range["start_date"])
            end_date = datetime.fromisoformat(date_range["end_date"])
            
            if report_type == "revenue":
                return await self._generate_revenue_report(start_date, end_date)
            elif report_type == "payments":
                return await self._generate_payments_report(start_date, end_date)
            elif report_type == "subscriptions":
                return await self._generate_subscriptions_report(start_date, end_date)
            else:
                return {"success": False, "error": "Invalid report type"}
                
        except Exception as e:
            logger.error(f"Error generating financial report: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_revenue_report(self, start_date: datetime, 
                                     end_date: datetime) -> Dict[str, Any]:
        """Generate revenue report"""
        # Mock revenue data
        return {
            "success": True,
            "report": {
                "total_revenue": "1250000.00",
                "currency": "MXN",
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "breakdown": {
                    "subscriptions": "1000000.00",
                    "one_time_payments": "250000.00"
                },
                "by_plan": {
                    "basic": "300000.00",
                    "professional": "700000.00",
                    "enterprise": "250000.00"
                },
                "growth_rate": "15.2%"
            }
        }

# Global payments service
def get_payments_service(db) -> PaymentsService:
    """Get payments service instance"""
    return PaymentsService(db)