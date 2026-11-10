import hashlib, json
from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI()
store: dict[str, dict] = {}  # practice only: key -> {hash, response}

class CreditRequestIn(BaseModel):
    lender_id: str = Field(min_length=1)
    borrower_ref: str = Field(min_length=1, max_length=64)
    loan_amount: int = Field(gt=0)

def body_hash(body: CreditRequestIn) -> str:
    return hashlib.sha256(json.dumps(body.model_dump(), sort_keys=True).encode()).hexdigest()

@app.post("/credit-requests", status_code=201)
def create_credit_request(
    body: CreditRequestIn,
    response: Response,
    idempotency_key: str = Header(..., min_length=8, max_length=128),
) -> dict:
    h = body_hash(body)
    seen = store.get(idempotency_key)
    if seen:
        if seen["hash"] != h:
            raise HTTPException(status_code=409, detail="Key reused with a different body")
        response.status_code = 200
        return seen["response"]
    new = {"id": f"CR-{len(store) + 1001}", "status": "RECEIVED", **body.model_dump()}
    store[idempotency_key] = {"hash": h, "response": new}
    return new