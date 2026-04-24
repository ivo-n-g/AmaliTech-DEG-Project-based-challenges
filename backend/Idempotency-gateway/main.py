from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel
import asyncio
import time
from Storage import get_transaction, save_transaction

app = FastAPI(title="FinSafe Idempotency Gateway")
request_lock = asyncio.Lock()

#Define exactly what the data should look like
class PaymentData(BaseModel):
    amount: int
    currency: str = "GHS"

    # This tells Swagger UI to pre-fill the white box
    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": 100,
                "currency": "GHS"
            }
        }
    }

@app.post("/process-payment")
async def process_payment(
    body: PaymentData,  # We use our strict model here
    response: Response,
    idempotency_key: str = Header(None)
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    # Convert the strict model back into a standard dictionary for our storage logic
    payload_dict = body.model_dump()

    async with request_lock:
        existing = get_transaction(idempotency_key)

        if existing:
            if existing["payload"] != payload_dict:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key already used for a different request body."
                )
            
            response.headers["X-Cache-Hit"] = "true"
            return existing["response"]

        # --- Simulate Bank Processing ---
        await asyncio.sleep(2) 

        charge_result = {
            "status": "success",
            "message": f"Charged {payload_dict.get('amount')} {payload_dict.get('currency')}",
            "amount": payload_dict.get("amount"),
            "currency": payload_dict.get("currency"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        save_transaction(idempotency_key, payload_dict, charge_result)

        return charge_result