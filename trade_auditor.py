import os
import math
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI

class TradeAuditor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: OpenAI API Key not found. Advisor layer will be disabled.")

    def calculate_rr(self, entry: float, target: float, sl: float) -> float:
        """
        Compute RR based on a specific target.
        """
        if entry == sl:
            return 0.0
        
        reward = abs(target - entry)
        risk = abs(entry - sl)
        
        if risk == 0:
             return 0.0

        return round(reward / risk, 2)

    def get_verdict(self, rr: float) -> str:
        if rr >= 1.5:
            return "SIGNAL IS MASSIVE"
        elif 1.0 <= rr < 1.5:
            return "SIGNAL IS SUPER"
        elif 0.8 <= rr < 1.0:
            return "SIGNAL IS GOOD"
        else:
            return "SIGNAL REJECTED"

    def calculate_position(self, entry: float, sl: float, capital: float, risk_pct: float) -> Dict[str, float]:
        """
        Calculate Position Size based on Risk.
        Risk Amount = Capital * (Risk% / 100)
        Position Size (Units) = Risk Amount / |Entry - SL|
        """
        if entry == sl:
            return {"error": "Entry equals SL"}
        
        risk_amount = capital * (risk_pct / 100)
        price_risk_per_unit = abs(entry - sl)
        
        units = risk_amount / price_risk_per_unit
        position_value = units * entry
        
        return {
            "risk_amount": round(risk_amount, 2),
            "units": units, # Keep precision for internal calc, round for display
            "position_value": round(position_value, 2)
        }

    async def get_advisor_response(self, context: Dict[str, Any], concern: str) -> str:
        if not self.client:
            return "AI Advisor unavailable: Missing OpenAI API Key."

        # Construct a rich prompt with the calculator details
        prompt = (
            f"You are a professional trading mentor. Review this trade plan:\n"
            f"Capital: ${context.get('capital')}\n"
            f"Risk per Trade: {context.get('risk_pct')}%\n"
            f"Entry: {context.get('entry')}, SL: {context.get('sl')}\n"
            f"Position Size: {round(context.get('calc', {}).get('units', 0), 4)} units\n"
            f"Risk Amount: ${context.get('calc', {}).get('risk_amount')}\n"
            f"Targets:\n"
        )
        
        for i, tp in enumerate(context.get('targets', []), 1):
            prompt += f"  TP{i}: {tp['price']} (RR: {tp['rr']}, Profit: ${tp['profit']})\n"

        if concern:
            prompt += f"\nUser Concern: \"{concern}\"\n"
        
        prompt += (
            "\nAddress the user's concern if provided, or give general feedback on the risk/reward profile. "
            "Comment on whether the position size is appropriate relative to capital. "
            "Keep the response professional, concise, and focused on risk management."
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful and cautious trading assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error contacting AI Advisor: {str(e)}"

    async def audit_trade(self, 
                          entry: float, 
                          sl: float, 
                          tps: List[float], 
                          capital: float = 10000.0, 
                          risk_pct: float = 1.0, 
                          user_concern: Optional[str] = None) -> Dict[str, Any]:
        """
        Orchestrate the Calculator Logic and AI Advisor.
        """
        try:
            # 1. Position Sizing
            calc = self.calculate_position(entry, sl, capital, risk_pct)
            if "error" in calc:
                return calc
            
            units = calc["units"]
            
            # 2. Analyze each TP
            targets_analysis = []
            max_rr = 0.0
            
            for tp_price in tps:
                if tp_price == 0: continue # Skip empty TPs
                
                rr = self.calculate_rr(entry, tp_price, sl)
                profit_per_unit = abs(tp_price - entry)
                total_profit = profit_per_unit * units
                roi = (total_profit / capital) * 100
                
                targets_analysis.append({
                    "price": tp_price,
                    "rr": rr,
                    "profit": round(total_profit, 2),
                    "roi": round(roi, 2)
                })
                
                if rr > max_rr:
                    max_rr = rr

            verdict = self.get_verdict(max_rr)

            result = {
                "input": {"entry": entry, "sl": sl, "capital": capital, "risk_pct": risk_pct},
                "calc": calc,
                "targets": targets_analysis,
                "verdict": verdict,
                "max_rr": max_rr
            }
            
            # 3. AI Advisor (Pass the whole context)
            if user_concern or True: # Always get advice if calc is successful
                 advisor_response = await self.get_advisor_response(result, user_concern)
                 result["advisor_response"] = advisor_response

            return result

        except Exception as e:
            return {"error": str(e)}
