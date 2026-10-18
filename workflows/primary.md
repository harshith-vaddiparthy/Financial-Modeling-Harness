# Primary workflow

1. Identify the company, business model, currency, projection start/horizon and output destination. Locate historical sources and separate closing balances from forecast drivers. Complete intake when required input fields and their source classes are known.
2. Prepare a private model JSON. Record actuals with document/row references; record assumptions with explicit rationale and dates. Use the input contract. Ask for a missing material target or input, or continue with a clearly disclosed assumption when the task supports one. The validator must accept the input and opening balance.
3. Run all requested scenarios with `finance_run` or `python3 -m harness run`. Review hiring capacity, acquisition budgets, cash timing, debt/funding events and unit economics against the company's evidence. Numerical balance is not proof of a plausible business plan.
4. Recalculate sensitivities for uncertain drivers. A new decision creates a new saved input and run; preserve earlier evidence. Complete interpretation when every requested business question has a sourced explanation or a precise unresolved input.
5. Verify the saved run with `finance_verify` or the CLI. Deliver its report and artifacts against the output contract, including caveats and any cash deficit. Complete only after fresh verification passes for the delivered run.
