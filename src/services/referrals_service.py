"""
HuntRED® v2 - Referrals Service
Complete referral program and commission management system
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class ReferralStatus(Enum):
    PENDING = "pending"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    PAID = "paid"
    EXPIRED = "expired"
    REJECTED = "rejected"

class ReferralType(Enum):
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    PARTNER = "partner"
    AFFILIATE = "affiliate"

class CommissionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"

class ReferralsService:
    """Complete referral program management"""
    
    def __init__(self, db):
        self.db = db
        
        # Referral program configuration
        self.referral_programs = {
            "customer_referral": {
                "name": "Programa de Referidos Clientes",
                "commission_type": "percentage",
                "commission_rate": Decimal("0.10"),  # 10% of first payment
                "minimum_payout": Decimal("500.00"),
                "qualification_period": 30,  # days
                "expiration_period": 90,  # days
                "max_referrals_per_month": 10,
                "bonus_tiers": {
                    5: Decimal("1000.00"),   # Bonus for 5 referrals
                    10: Decimal("2500.00"),  # Bonus for 10 referrals
                    20: Decimal("5000.00")   # Bonus for 20 referrals
                }
            },
            "employee_referral": {
                "name": "Programa de Referidos Empleados",
                "commission_type": "fixed",
                "commission_amount": Decimal("2000.00"),
                "minimum_payout": Decimal("1000.00"),
                "qualification_period": 90,  # days (employee must stay)
                "expiration_period": 180,  # days
                "max_referrals_per_month": 5,
                "bonus_tiers": {
                    3: Decimal("1500.00"),   # Bonus for 3 referrals
                    5: Decimal("3000.00"),   # Bonus for 5 referrals
                    10: Decimal("7500.00")   # Bonus for 10 referrals
                }
            },
            "partner_referral": {
                "name": "Programa de Socios",
                "commission_type": "percentage",
                "commission_rate": Decimal("0.15"),  # 15% recurring
                "minimum_payout": Decimal("1000.00"),
                "qualification_period": 7,   # days
                "expiration_period": 365,  # days
                "max_referrals_per_month": 50,
                "recurring_commission": True,
                "recurring_months": 12
            },
            "affiliate_referral": {
                "name": "Programa de Afiliados",
                "commission_type": "percentage",
                "commission_rate": Decimal("0.20"),  # 20% of first payment
                "minimum_payout": Decimal("2000.00"),
                "qualification_period": 14,  # days
                "expiration_period": 60,   # days
                "max_referrals_per_month": 100,
                "performance_bonuses": {
                    "bronze": {"min_referrals": 10, "bonus_rate": Decimal("0.05")},
                    "silver": {"min_referrals": 25, "bonus_rate": Decimal("0.10")},
                    "gold": {"min_referrals": 50, "bonus_rate": Decimal("0.15")}
                }
            }
        }
    
    async def create_referral(self, referral_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new referral"""
        try:
            referral_id = str(uuid.uuid4())
            
            # Extract referral information
            referrer_info = referral_data["referrer_info"]
            referred_info = referral_data["referred_info"]
            referral_type = ReferralType(referral_data.get("type", "customer"))
            program_config = self.referral_programs[f"{referral_type.value}_referral"]
            
            # Generate referral code
            referral_code = self._generate_referral_code(referrer_info, referral_type)
            
            # Create referral record
            referral = {
                "id": referral_id,
                "referral_code": referral_code,
                "referrer_info": referrer_info,
                "referred_info": referred_info,
                "type": referral_type.value,
                "status": ReferralStatus.PENDING.value,
                "program_config": program_config,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=program_config["expiration_period"]),
                "qualification_deadline": datetime.now() + timedelta(days=program_config["qualification_period"]),
                "metadata": {
                    "source": referral_data.get("source", "direct"),
                    "campaign": referral_data.get("campaign"),
                    "notes": referral_data.get("notes")
                }
            }
            
            # Validate referral limits
            validation_result = await self._validate_referral_limits(referrer_info, referral_type)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "referral_id": referral_id
                }
            
            # Save to database
            # await self._save_referral(referral)
            
            # Send notifications
            await self._send_referral_notifications(referral)
            
            logger.info(f"Referral {referral_id} created successfully")
            
            return {
                "success": True,
                "referral_id": referral_id,
                "referral_code": referral_code,
                "referral": referral,
                "tracking_url": f"https://huntred.com/ref/{referral_code}"
            }
            
        except Exception as e:
            logger.error(f"Error creating referral: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_referral_code(self, referrer_info: Dict[str, Any], 
                               referral_type: ReferralType) -> str:
        """Generate unique referral code"""
        
        # Create base string
        base_string = f"{referrer_info.get('id', '')}{referrer_info.get('email', '')}{datetime.now().isoformat()}"
        
        # Generate hash
        hash_object = hashlib.md5(base_string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Create referral code
        type_prefix = {
            ReferralType.CUSTOMER: "CUS",
            ReferralType.EMPLOYEE: "EMP", 
            ReferralType.PARTNER: "PAR",
            ReferralType.AFFILIATE: "AFF"
        }
        
        return f"{type_prefix[referral_type]}{hash_hex[:8].upper()}"
    
    async def _validate_referral_limits(self, referrer_info: Dict[str, Any], 
                                      referral_type: ReferralType) -> Dict[str, Any]:
        """Validate referral limits"""
        
        program_config = self.referral_programs[f"{referral_type.value}_referral"]
        max_monthly = program_config["max_referrals_per_month"]
        
        # Check monthly limit (mock implementation)
        current_month_referrals = await self._get_monthly_referrals_count(
            referrer_info.get("id"), referral_type
        )
        
        if current_month_referrals >= max_monthly:
            return {
                "valid": False,
                "error": f"Monthly referral limit exceeded ({max_monthly})"
            }
        
        # Check for duplicate referrals
        existing_referral = await self._check_duplicate_referral(
            referrer_info.get("id"), referrer_info.get("email")
        )
        
        if existing_referral:
            return {
                "valid": False,
                "error": "Duplicate referral detected"
            }
        
        return {"valid": True}
    
    async def _get_monthly_referrals_count(self, referrer_id: str, 
                                         referral_type: ReferralType) -> int:
        """Get monthly referrals count (mock implementation)"""
        # In real implementation, query database
        return 3  # Mock count
    
    async def _check_duplicate_referral(self, referrer_id: str, referred_email: str) -> bool:
        """Check for duplicate referral (mock implementation)"""
        # In real implementation, query database
        return False  # Mock result
    
    async def _send_referral_notifications(self, referral: Dict[str, Any]) -> None:
        """Send referral notifications"""
        try:
            # Send email to referrer
            await self._send_referrer_notification(referral)
            
            # Send email to referred person
            await self._send_referred_notification(referral)
            
            logger.info(f"Referral notifications sent for {referral['id']}")
            
        except Exception as e:
            logger.error(f"Error sending referral notifications: {e}")
    
    async def _send_referrer_notification(self, referral: Dict[str, Any]) -> None:
        """Send notification to referrer"""
        # Mock email sending
        logger.info(f"Referrer notification sent to {referral['referrer_info'].get('email')}")
    
    async def _send_referred_notification(self, referral: Dict[str, Any]) -> None:
        """Send notification to referred person"""
        # Mock email sending
        logger.info(f"Referred notification sent to {referral['referred_info'].get('email')}")
    
    async def qualify_referral(self, referral_id: str, 
                             qualification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify a referral (when referred person takes action)"""
        try:
            # Get referral
            referral = await self._get_referral(referral_id)
            
            if not referral:
                return {"success": False, "error": "Referral not found"}
            
            if referral["status"] != ReferralStatus.PENDING.value:
                return {"success": False, "error": "Referral already processed"}
            
            # Check qualification deadline
            if datetime.now() > referral["qualification_deadline"]:
                referral["status"] = ReferralStatus.EXPIRED.value
                return {"success": False, "error": "Referral qualification period expired"}
            
            # Update referral status
            referral["status"] = ReferralStatus.QUALIFIED.value
            referral["qualified_at"] = datetime.now()
            referral["qualification_data"] = qualification_data
            
            # Calculate potential commission
            commission = await self._calculate_commission(referral, qualification_data)
            referral["commission"] = commission
            
            # Save updated referral
            # await self._save_referral(referral)
            
            # Send qualification notifications
            await self._send_qualification_notifications(referral)
            
            logger.info(f"Referral {referral_id} qualified successfully")
            
            return {
                "success": True,
                "referral_id": referral_id,
                "status": "qualified",
                "commission": commission
            }
            
        except Exception as e:
            logger.error(f"Error qualifying referral: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_referral(self, referral_id: str) -> Optional[Dict[str, Any]]:
        """Get referral by ID (mock implementation)"""
        # In real implementation, query from database
        return {
            "id": referral_id,
            "status": ReferralStatus.PENDING.value,
            "qualification_deadline": datetime.now() + timedelta(days=30),
            "program_config": self.referral_programs["customer_referral"]
        }
    
    async def _calculate_commission(self, referral: Dict[str, Any], 
                                  qualification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate commission for referral"""
        
        program_config = referral["program_config"]
        commission_type = program_config["commission_type"]
        
        commission = {
            "type": commission_type,
            "amount": Decimal("0.00"),
            "currency": "MXN",
            "recurring": program_config.get("recurring_commission", False),
            "recurring_months": program_config.get("recurring_months", 0)
        }
        
        if commission_type == "percentage":
            # Percentage-based commission
            transaction_amount = Decimal(str(qualification_data.get("transaction_amount", 0)))
            commission_rate = program_config["commission_rate"]
            commission["amount"] = transaction_amount * commission_rate
            
        elif commission_type == "fixed":
            # Fixed commission
            commission["amount"] = program_config["commission_amount"]
        
        # Apply performance bonuses if applicable
        if "performance_bonuses" in program_config:
            bonus = await self._calculate_performance_bonus(referral, program_config)
            commission["bonus"] = bonus
            commission["amount"] += bonus
        
        return commission
    
    async def _calculate_performance_bonus(self, referral: Dict[str, Any], 
                                         program_config: Dict[str, Any]) -> Decimal:
        """Calculate performance bonus"""
        
        referrer_id = referral["referrer_info"].get("id")
        
        # Get referrer's total referrals this month
        monthly_referrals = await self._get_monthly_referrals_count(
            referrer_id, ReferralType(referral["type"])
        )
        
        performance_bonuses = program_config["performance_bonuses"]
        bonus = Decimal("0.00")
        
        # Check which tier applies
        for tier, config in performance_bonuses.items():
            if monthly_referrals >= config["min_referrals"]:
                bonus = referral["commission"]["amount"] * config["bonus_rate"]
        
        return bonus
    
    async def _send_qualification_notifications(self, referral: Dict[str, Any]) -> None:
        """Send qualification notifications"""
        # Mock notification sending
        logger.info(f"Qualification notifications sent for referral {referral['id']}")
    
    async def convert_referral(self, referral_id: str, 
                             conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a qualified referral to paid status"""
        try:
            # Get referral
            referral = await self._get_referral(referral_id)
            
            if not referral:
                return {"success": False, "error": "Referral not found"}
            
            if referral["status"] != ReferralStatus.QUALIFIED.value:
                return {"success": False, "error": "Referral not qualified"}
            
            # Update referral status
            referral["status"] = ReferralStatus.CONVERTED.value
            referral["converted_at"] = datetime.now()
            referral["conversion_data"] = conversion_data
            
            # Create commission record
            commission_id = await self._create_commission_record(referral, conversion_data)
            referral["commission_id"] = commission_id
            
            # Save updated referral
            # await self._save_referral(referral)
            
            # Send conversion notifications
            await self._send_conversion_notifications(referral)
            
            logger.info(f"Referral {referral_id} converted successfully")
            
            return {
                "success": True,
                "referral_id": referral_id,
                "commission_id": commission_id,
                "status": "converted"
            }
            
        except Exception as e:
            logger.error(f"Error converting referral: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_commission_record(self, referral: Dict[str, Any], 
                                      conversion_data: Dict[str, Any]) -> str:
        """Create commission record"""
        
        commission_id = str(uuid.uuid4())
        
        commission = {
            "id": commission_id,
            "referral_id": referral["id"],
            "referrer_info": referral["referrer_info"],
            "amount": referral["commission"]["amount"],
            "currency": referral["commission"]["currency"],
            "type": referral["commission"]["type"],
            "status": CommissionStatus.PENDING.value,
            "created_at": datetime.now(),
            "due_date": datetime.now() + timedelta(days=30),  # Pay within 30 days
            "conversion_data": conversion_data,
            "recurring": referral["commission"].get("recurring", False),
            "recurring_months": referral["commission"].get("recurring_months", 0)
        }
        
        # Save commission record
        # await self._save_commission(commission)
        
        return commission_id
    
    async def _send_conversion_notifications(self, referral: Dict[str, Any]) -> None:
        """Send conversion notifications"""
        # Mock notification sending
        logger.info(f"Conversion notifications sent for referral {referral['id']}")
    
    async def process_commission_payment(self, commission_id: str) -> Dict[str, Any]:
        """Process commission payment"""
        try:
            # Get commission record
            commission = await self._get_commission(commission_id)
            
            if not commission:
                return {"success": False, "error": "Commission not found"}
            
            if commission["status"] != CommissionStatus.APPROVED.value:
                return {"success": False, "error": "Commission not approved"}
            
            # Check minimum payout threshold
            program_config = await self._get_program_config_for_commission(commission)
            minimum_payout = program_config["minimum_payout"]
            
            if commission["amount"] < minimum_payout:
                return {
                    "success": False, 
                    "error": f"Amount below minimum payout threshold ({minimum_payout})"
                }
            
            # Process payment
            payment_result = await self._process_commission_payment(commission)
            
            if payment_result["success"]:
                # Update commission status
                commission["status"] = CommissionStatus.PAID.value
                commission["paid_at"] = datetime.now()
                commission["payment_reference"] = payment_result["payment_reference"]
                
                # Save updated commission
                # await self._save_commission(commission)
                
                # Send payment notifications
                await self._send_payment_notifications(commission)
                
                logger.info(f"Commission {commission_id} paid successfully")
                
                return {
                    "success": True,
                    "commission_id": commission_id,
                    "payment_reference": payment_result["payment_reference"],
                    "amount": commission["amount"]
                }
            else:
                return {
                    "success": False,
                    "error": payment_result["error"]
                }
                
        except Exception as e:
            logger.error(f"Error processing commission payment: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_commission(self, commission_id: str) -> Optional[Dict[str, Any]]:
        """Get commission record (mock implementation)"""
        # In real implementation, query from database
        return {
            "id": commission_id,
            "referral_id": "test_referral",
            "amount": Decimal("1500.00"),
            "currency": "MXN",
            "status": CommissionStatus.APPROVED.value,
            "referrer_info": {
                "id": "test_referrer",
                "email": "referrer@example.com",
                "name": "Test Referrer"
            }
        }
    
    async def _get_program_config_for_commission(self, commission: Dict[str, Any]) -> Dict[str, Any]:
        """Get program configuration for commission"""
        # Mock implementation
        return self.referral_programs["customer_referral"]
    
    async def _process_commission_payment(self, commission: Dict[str, Any]) -> Dict[str, Any]:
        """Process commission payment"""
        try:
            # Mock payment processing
            payment_reference = f"PAY_{uuid.uuid4().hex[:8].upper()}"
            
            # In real implementation, integrate with payment processor
            # - Create bank transfer
            # - Process PayPal payment
            # - Generate check
            # etc.
            
            return {
                "success": True,
                "payment_reference": payment_reference,
                "payment_method": "bank_transfer",
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing commission payment: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_payment_notifications(self, commission: Dict[str, Any]) -> None:
        """Send payment notifications"""
        # Mock notification sending
        logger.info(f"Payment notifications sent for commission {commission['id']}")
    
    async def get_referral_dashboard(self, referrer_id: str) -> Dict[str, Any]:
        """Get referral dashboard data"""
        try:
            # Get referrer's referrals
            referrals = await self._get_referrer_referrals(referrer_id)
            
            # Calculate statistics
            stats = {
                "total_referrals": len(referrals),
                "pending_referrals": len([r for r in referrals if r["status"] == "pending"]),
                "qualified_referrals": len([r for r in referrals if r["status"] == "qualified"]),
                "converted_referrals": len([r for r in referrals if r["status"] == "converted"]),
                "total_commissions": sum([r.get("commission", {}).get("amount", 0) for r in referrals]),
                "paid_commissions": sum([r.get("commission", {}).get("amount", 0) for r in referrals if r["status"] == "paid"]),
                "pending_commissions": sum([r.get("commission", {}).get("amount", 0) for r in referrals if r["status"] in ["qualified", "converted"]])
            }
            
            # Get monthly performance
            monthly_performance = await self._get_monthly_performance(referrer_id)
            
            # Get leaderboard position
            leaderboard_position = await self._get_leaderboard_position(referrer_id)
            
            return {
                "success": True,
                "referrer_id": referrer_id,
                "stats": stats,
                "referrals": referrals,
                "monthly_performance": monthly_performance,
                "leaderboard_position": leaderboard_position,
                "next_tier_requirements": await self._get_next_tier_requirements(referrer_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting referral dashboard: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_referrer_referrals(self, referrer_id: str) -> List[Dict[str, Any]]:
        """Get referrals for a specific referrer"""
        # Mock implementation
        return [
            {
                "id": "ref_1",
                "status": "converted",
                "created_at": datetime.now() - timedelta(days=30),
                "commission": {"amount": Decimal("1500.00"), "currency": "MXN"}
            },
            {
                "id": "ref_2", 
                "status": "qualified",
                "created_at": datetime.now() - timedelta(days=15),
                "commission": {"amount": Decimal("2000.00"), "currency": "MXN"}
            }
        ]
    
    async def _get_monthly_performance(self, referrer_id: str) -> Dict[str, Any]:
        """Get monthly performance data"""
        # Mock implementation
        return {
            "current_month": {
                "referrals": 5,
                "conversions": 3,
                "commissions": "4500.00"
            },
            "last_month": {
                "referrals": 3,
                "conversions": 2,
                "commissions": "3000.00"
            },
            "growth_rate": "50.0%"
        }
    
    async def _get_leaderboard_position(self, referrer_id: str) -> Dict[str, Any]:
        """Get leaderboard position"""
        # Mock implementation
        return {
            "position": 5,
            "total_referrers": 100,
            "percentile": 95,
            "tier": "silver"
        }
    
    async def _get_next_tier_requirements(self, referrer_id: str) -> Dict[str, Any]:
        """Get requirements for next tier"""
        # Mock implementation
        return {
            "current_tier": "silver",
            "next_tier": "gold",
            "requirements": {
                "referrals_needed": 5,
                "conversions_needed": 3,
                "time_remaining": "15 days"
            }
        }

# Global referrals service
def get_referrals_service(db) -> ReferralsService:
    """Get referrals service instance"""
    return ReferralsService(db)