# shared

Code reused by **two or more** feature modules. No feature-specific business logic here.

## Built

```
shared/email/         # Provider-agnostic email sender (password recovery, D23)
├── base.py           #   EmailSender interface
├── smtp.py           #   SMTP delivery (stdlib smtplib; Gmail App Password)
├── console.py        #   dev fallback — logs the message, never sends
└── factory.py        #   get_email_sender() selects by EMAIL_ENABLED
```

## Planned

```
shared/llm/           # Provider-agnostic LLM (Ollama / OpenAI) — Layer 2 of analysis
```

Create `shared/llm/` when implementing analysis Layer 2 (`docs/ARCHITECTURE.md`). It follows the same base/impl/factory shape as `shared/email/`.
