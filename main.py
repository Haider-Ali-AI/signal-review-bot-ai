import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from trade_auditor import TradeAuditor
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Signal Review Bot API", description="Smart Trade Calculator & Advisor API")

auditor = TradeAuditor()

class TradeSignal(BaseModel):
    entry: float
    sl: float
    tp_1: float
    tp_2: Optional[float] = 0.0
    tp_3: Optional[float] = 0.0
    capital: Optional[float] = 10000.0
    risk_pct: Optional[float] = 1.0
    user_concern: Optional[str] = None

class TargetAnalysis(BaseModel):
    price: float
    rr: float
    profit: float
    roi: float

class CalculatorResult(BaseModel):
    risk_amount: float
    units: float
    position_value: float

class AuditResult(BaseModel):
    verdict: str
    max_rr: float
    calc: CalculatorResult
    targets: List[TargetAnalysis]
    advisor_response: Optional[str] = None

@app.post("/review", response_model=AuditResult)
async def review_signal(signal: TradeSignal):
    tps = [signal.tp_1]
    if signal.tp_2: tps.append(signal.tp_2)
    if signal.tp_3: tps.append(signal.tp_3)
    
    result = await auditor.audit_trade(
        entry=signal.entry,
        sl=signal.sl,
        tps=tps,
        capital=signal.capital,
        risk_pct=signal.risk_pct,
        user_concern=signal.user_concern
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
