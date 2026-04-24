from fastapi import FastAPI, Header, HTTPException, Response
import asyncio
import time
from Storage import get_transaction, save_transaction

app = FastAPI(title="FinSafe Idempotency Gateway")

# Async lock to prevent race conditions 
request_lock = asyncio.Lock()

@app.post("/process-payment")
async def process_payment(
    body: dict,  
    response: Response,
    idempotency_key: str = Header(None)
):
    # Validate header presence
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    # Use lock to handle overlapping identical requests
    async with request_lock:
        existing = get_transaction(idempotency_key)

        if existing:
            # Check if this is a fraud/error attempt (different body, same key)
            if existing["payload"] != body:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key already used for a different request body."
                )
            
            # Return cached response for legitimate retries
            response.headers["X-Cache-Hit"] = "true"
            return existing["response"]

        # --- Simulate Bank Processing  ---
        await asyncio.sleep(2) 

        # Generate successful response
        charge_result = {
            "status": "success",
            "message": f"Charged {body.get('amount')} {body.get('currency', 'GHS')}",
            "amount": body.get("amount"),
            "currency": body.get("currency", "GHS"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Persist for idempotency
        save_transaction(idempotency_key, body, charge_result)

        return charge_result