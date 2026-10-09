# APPI website

Public product site plus the signed-in operator dashboard.

```bash
npm install
npm run dev
```

| Route | What it is |
| --- | --- |
| `/` | Marketing site |
| `/product` | How Appi works |
| `/security` | Guardian, kill switch, audit |
| `/download` | Windows install and pairing |
| `/app` | Operator (sign-in required) |

The FastAPI brain should be on `http://localhost:8000`. Copy `.env.example` at the repo root.
