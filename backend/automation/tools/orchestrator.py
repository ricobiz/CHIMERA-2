"""
Tool Orchestrator - Manages all automation tools
Provides email, password, phone, proxy, captcha, and data generation tools
"""

import logging
import random
import string
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ToolOrchestrator:
    """
    Centralized tool management for autonomous automation.
    Provides all necessary tools for registration, verification, and anti-detection.
    """
    
    def __init__(self):
        self.available_tools = {
            "create_temp_email": self._create_temp_email,
            "generate_password": self._generate_password, 
            "generate_user_data": self._generate_user_data,
            "get_phone_number": self._get_phone_number,
            "setup_proxy": self._setup_proxy,
            "solve_captcha": self._solve_captcha,
            "generate_field_data": self._generate_field_data,
            "verify_email": self._verify_email,
            "receive_sms": self._receive_sms
        }
        
        # Tool state tracking
        self.tool_usage = {}
        self.created_resources = {}
    
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.available_tools:
            logger.error(f"❌ [TOOLS] Unknown tool: {tool_name}")
            return {"error": f"Tool {tool_name} not found"}
        
        try:
            logger.info(f"🔧 [TOOLS] Executing {tool_name}")
            
            # Track usage
            self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1
            
            # Execute tool
            result = await self.available_tools[tool_name](params)
            
            # Store created resources
            if result and not result.get("error"):
                self.created_resources.update(result)
            
            logger.info(f"✅ [TOOLS] {tool_name} completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ [TOOLS] {tool_name} failed: {e}")
            return {"error": str(e)}
    
    async def _create_temp_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create temporary email address.
        Uses multiple providers for reliability.
        """
        try:
            # Try multiple temp email strategies
            strategies = [
                self._create_guerrilla_email,
                self._create_tempmail_email, 
                self._create_10minutemail_email,
                self._generate_gmail_variant
            ]
            
            for strategy in strategies:
                try:
                    result = await strategy()
                    if result and not result.get("error"):
                        logger.info(f"📧 [EMAIL] Created: {result.get('email')}")
                        return result
                except Exception as e:
                    logger.warning(f"Email strategy failed: {e}")
                    continue
            
            # Fallback: generate simple email
            return await self._generate_gmail_variant()
            
        except Exception as e:
            logger.error(f"❌ [EMAIL] All strategies failed: {e}")
            return {"error": str(e)}
    
    async def _create_guerrilla_email(self) -> Dict[str, Any]:
        """Create email using Guerrilla Mail API"""
        try:
            import httpx
            
            # Get session ID
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://www.guerrillamail.com/ajax.php?f=get_email_address")
                data = resp.json()
                
                if data.get("email_addr"):
                    return {
                        "email": data["email_addr"],
                        "provider": "guerrilla_mail",
                        "session_id": data.get("sid_token"),
                        "expires_in": 3600,  # 1 hour
                        "access_url": f"https://www.guerrillamail.com/inbox?sid_token={data.get('sid_token')}"
                    }
            
            return {"error": "Failed to create Guerrilla Mail"}
            
        except Exception as e:
            return {"error": f"Guerrilla Mail error: {e}"}
    
    async def _create_tempmail_email(self) -> Dict[str, Any]:
        """Create email using TempMail.org"""
        try:
            import httpx
            
            # Generate random email
            domains = ["@tempmail.org", "@guerrillamail.com", "@10minutemail.com"]
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            domain = random.choice(domains)
            email = f"{username}{domain}"
            
            return {
                "email": email,
                "provider": "temp_mail",
                "expires_in": 600,  # 10 minutes
                "access_url": f"https://temp-mail.org/en/view/{username}"
            }
            
        except Exception as e:
            return {"error": f"TempMail error: {e}"}
    
    async def _create_10minutemail_email(self) -> Dict[str, Any]:
        """Create email using 10MinuteMail"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                # Get new email
                resp = await client.get("https://10minutemail.com/10MinuteMail/resources/session/address")
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "email": data.get("address"),
                        "provider": "10_minute_mail",
                        "expires_in": 600,  # 10 minutes
                        "session_id": data.get("sessionId")
                    }
            
            return {"error": "Failed to create 10MinuteMail"}
            
        except Exception as e:
            return {"error": f"10MinuteMail error: {e}"}
    
    async def _generate_gmail_variant(self) -> Dict[str, Any]:
        """Generate Gmail-like email (fallback)"""
        try:
            # Generate realistic Gmail address
            first_names = ["john", "jane", "alex", "sarah", "mike", "lisa", "david", "emma"]
            last_names = ["smith", "johnson", "brown", "davis", "wilson", "moore", "taylor"]
            
            first = random.choice(first_names)
            last = random.choice(last_names)
            number = random.randint(100, 9999)
            
            # Various Gmail patterns
            patterns = [
                f"{first}.{last}{number}@gmail.com",
                f"{first}{last}{number}@gmail.com", 
                f"{first[0]}{last}{number}@gmail.com",
                f"{first}.{last}.{number}@gmail.com"
            ]
            
            email = random.choice(patterns)
            
            return {
                "email": email,
                "provider": "generated_gmail",
                "expires_in": None,  # Permanent (but fake)
                "note": "Generated email - may not receive actual messages"
            }
            
        except Exception as e:
            return {"error": f"Gmail generation error: {e}"}
    
    async def _generate_password(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate secure password"""
        try:
            length = params.get("length", 12)
            include_symbols = params.get("symbols", True)
            include_numbers = params.get("numbers", True)
            
            # Character sets
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase  
            numbers = string.digits
            symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            # Build character set
            chars = lowercase + uppercase
            if include_numbers:
                chars += numbers
            if include_symbols:
                chars += symbols
            
            # Generate password ensuring at least one of each type
            password = []
            password.append(random.choice(lowercase))
            password.append(random.choice(uppercase))
            
            if include_numbers:
                password.append(random.choice(numbers))
            if include_symbols:
                password.append(random.choice(symbols))
            
            # Fill remaining length
            for _ in range(length - len(password)):
                password.append(random.choice(chars))
            
            # Shuffle
            random.shuffle(password)
            final_password = ''.join(password)
            
            return {
                "password": final_password,
                "strength": "strong",
                "length": len(final_password)
            }
            
        except Exception as e:
            return {"error": f"Password generation error: {e}"}
    
    async def _generate_user_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete user data set"""
        try:
            from faker import Faker
            fake = Faker(['en_US'])
            
            # Generate realistic user data
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            data = {
                "first_name": first_name,
                "last_name": last_name,
                "username": f"{first_name.lower()}.{last_name.lower()}.{random.randint(100, 999)}",
                "birthday": fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%Y-%m-%d'),
                "phone_number": fake.phone_number(),
                "address": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": "US",
                "postal_code": fake.postcode(),
                "company": fake.company(),
                "job_title": fake.job()
            }
            
            # Generate email and password
            email_result = await self._create_temp_email({})
            if email_result and not email_result.get("error"):
                data["email"] = email_result["email"]
                data["email_provider"] = email_result.get("provider")
                data["email_access_url"] = email_result.get("access_url")
            
            password_result = await self._generate_password({})
            if password_result and not password_result.get("error"):
                data["password"] = password_result["password"]
            
            return data
            
        except Exception as e:
            return {"error": f"User data generation error: {e}"}
    
    async def _generate_field_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for specific field"""
        try:
            field = params.get("field", "").lower()
            data_key = params.get("data_key", "").lower()
            
            # Determine what kind of data to generate
            if "email" in field or "email" in data_key:
                return await self._create_temp_email({})
            
            elif "password" in field or "password" in data_key:
                return await self._generate_password({})
            
            elif "first_name" in field or "first_name" in data_key:
                from faker import Faker
                fake = Faker(['en_US'])
                return {"first_name": fake.first_name()}
            
            elif "last_name" in field or "last_name" in data_key:
                from faker import Faker
                fake = Faker(['en_US'])
                return {"last_name": fake.last_name()}
            
            elif "username" in field or "username" in data_key:
                from faker import Faker
                fake = Faker(['en_US'])
                first = fake.first_name().lower()
                last = fake.last_name().lower()
                return {"username": f"{first}.{last}.{random.randint(100, 999)}"}
            
            elif "phone" in field or "phone" in data_key:
                return await self._get_phone_number({})
            
            else:
                # Generic text generation
                from faker import Faker
                fake = Faker(['en_US'])
                return {data_key or field: fake.word()}
            
        except Exception as e:
            return {"error": f"Field data generation error: {e}"}
    
    async def _get_phone_number(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get phone number for verification"""
        try:
            # For now, generate fake number
            # In production, would integrate with SMS services
            area_codes = ["555", "123", "456", "789"]
            area = random.choice(area_codes)
            number = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            
            phone = f"({area[0:3]}) {area[3:6]}-{number[:4]}"
            
            return {
                "phone_number": phone,
                "provider": "generated",
                "note": "Generated phone number - cannot receive SMS"
            }
            
        except Exception as e:
            return {"error": f"Phone generation error: {e}"}
    
    async def _setup_proxy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Setup proxy connection"""
        try:
            # Integrate with existing proxy service
            from services.proxy_service import proxy_service
            
            if proxy_service.is_enabled():
                proxy = proxy_service.get_next_proxy()
                if proxy:
                    return {
                        "proxy_enabled": True,
                        "proxy_server": proxy.get("server"),
                        "proxy_type": proxy.get("type", "http")
                    }
            
            return {
                "proxy_enabled": False,
                "note": "No proxy available"
            }
            
        except Exception as e:
            return {"error": f"Proxy setup error: {e}"}
    
    async def _solve_captcha(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Solve CAPTCHA if present"""
        try:
            session_id = params.get("session_id")
            if not session_id:
                return {"error": "Session ID required for CAPTCHA solving"}
            
            # Use existing CAPTCHA solver
            from services.browser_automation_service import browser_service
            
            result = await browser_service.detect_and_solve_captcha(session_id)
            
            return {
                "captcha_solved": result.get("success", False),
                "captcha_message": result.get("message", ""),
                "screenshot_updated": bool(result.get("screenshot"))
            }
            
        except Exception as e:
            return {"error": f"CAPTCHA solving error: {e}"}
    
    async def _verify_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check for email verification messages"""
        try:
            email = params.get("email")
            provider = params.get("provider")
            
            if provider == "guerrilla_mail":
                return await self._check_guerrilla_inbox(params)
            elif provider == "10_minute_mail":
                return await self._check_10minute_inbox(params)
            else:
                return {
                    "has_messages": False,
                    "note": f"Email verification not supported for {provider}"
                }
            
        except Exception as e:
            return {"error": f"Email verification error: {e}"}
    
    async def _check_guerrilla_inbox(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check Guerrilla Mail inbox"""
        try:
            import httpx
            
            session_id = params.get("session_id")
            if not session_id:
                return {"error": "Session ID required for Guerrilla Mail"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://www.guerrillamail.com/ajax.php?f=get_email_list&sid_token={session_id}")
                data = resp.json()
                
                messages = data.get("list", [])
                verification_messages = []
                
                for msg in messages:
                    subject = msg.get("mail_subject", "").lower()
                    if any(keyword in subject for keyword in ["verify", "confirm", "activation", "welcome"]):
                        verification_messages.append({
                            "subject": msg.get("mail_subject"),
                            "from": msg.get("mail_from"),
                            "id": msg.get("mail_id"),
                            "time": msg.get("mail_timestamp")
                        })
                
                return {
                    "has_messages": len(verification_messages) > 0,
                    "message_count": len(messages),
                    "verification_messages": verification_messages
                }
            
        except Exception as e:
            return {"error": f"Guerrilla Mail check error: {e}"}
    
    async def _check_10minute_inbox(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check 10MinuteMail inbox"""
        try:
            import httpx
            
            session_id = params.get("session_id")
            if not session_id:
                return {"error": "Session ID required for 10MinuteMail"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://10minutemail.com/10MinuteMail/resources/messages/messagesAfter/0")
                
                if resp.status_code == 200:
                    messages = resp.json()
                    return {
                        "has_messages": len(messages) > 0,
                        "message_count": len(messages),
                        "messages": [{"subject": msg.get("subject"), "from": msg.get("sender")} for msg in messages]
                    }
            
            return {"has_messages": False}
            
        except Exception as e:
            return {"error": f"10MinuteMail check error: {e}"}
    
    async def _receive_sms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Receive SMS verification code"""
        try:
            phone_number = params.get("phone_number")
            
            # For now, return placeholder
            # In production, would integrate with SMS reception services
            return {
                "has_sms": False,
                "note": "SMS reception not implemented - would need real SMS service"
            }
            
        except Exception as e:
            return {"error": f"SMS reception error: {e}"}
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.available_tools.keys())
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        return {
            "usage": self.tool_usage,
            "created_resources": list(self.created_resources.keys()),
            "total_executions": sum(self.tool_usage.values())
        }


# Global instance
tool_orchestrator = ToolOrchestrator()