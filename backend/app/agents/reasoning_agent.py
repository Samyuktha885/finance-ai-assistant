"""
Reasoning Agent: does the actual business-finance "thinking" — calculators for
concrete questions (break-even, EMI, cash reserve target, etc.) plus an LLM call
that synthesizes a final answer from the user's question + retrieved KB context
+ known facts, asking the LLM to self-report a confidence score with
justification (for explainability).

Two-step tool-calling design:
1. select_tool() — the LLM only DECIDES which calculator applies and extracts
   the numeric arguments. It never does arithmetic itself.
2. run_tool() — the REAL Python function computes the exact answer.
3. _phrase_calculation_result() — the LLM explains the exact result in plain
   language, but cannot alter the numbers.

This avoids LLM math errors on precise financial calculations.
"""
from app.llm import chat_completion_json


def emi_calculator(principal: float, annual_rate_pct: float, tenure_years: float) -> dict:
    """Standard reducing-balance EMI formula — see kb/docs/business_loan_types.md."""
    r = (annual_rate_pct / 100) / 12
    n = int(tenure_years * 12)
    if r == 0:
        emi = principal / n
    else:
        emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    total_payment = emi * n
    total_interest = total_payment - principal
    return {
        "emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "formula": "EMI = P * r * (1+r)^n / ((1+r)^n - 1), r = monthly rate, n = months",
    }


def break_even_point(fixed_costs: float, selling_price_per_unit: float, variable_cost_per_unit: float) -> dict:
    """See kb/docs/break_even_analysis.md."""
    contribution_margin = selling_price_per_unit - variable_cost_per_unit
    if contribution_margin <= 0:
        return {
            "error": "Selling price must exceed variable cost per unit for break-even to be reachable.",
            "contribution_margin_per_unit": round(contribution_margin, 2),
        }
    break_even_units = fixed_costs / contribution_margin
    break_even_revenue = break_even_units * selling_price_per_unit
    return {
        "break_even_units": round(break_even_units, 2),
        "break_even_revenue": round(break_even_revenue, 2),
        "contribution_margin_per_unit": round(contribution_margin, 2),
        "formula": "Break-even units = Fixed Costs / (Selling Price - Variable Cost per Unit)",
    }


def business_cash_reserve_target(monthly_fixed_expenses: float, months_of_cover: int = 6) -> dict:
    """See kb/docs/business_cash_reserve.md — default 6 months, adjustable for revenue stability."""
    target = monthly_fixed_expenses * months_of_cover
    return {
        "target_amount": round(target, 2),
        "months_of_cover": months_of_cover,
        "monthly_fixed_expenses_used": monthly_fixed_expenses,
    }


def working_capital_calculator(current_assets: float, current_liabilities: float) -> dict:
    """See kb/docs/working_capital_management.md."""
    working_capital = current_assets - current_liabilities
    status = "positive" if working_capital > 0 else ("negative" if working_capital < 0 else "break-even")
    return {
        "working_capital": round(working_capital, 2),
        "status": status,
        "formula": "Working Capital = Current Assets - Current Liabilities",
    }


def profit_margin_calculator(revenue: float, cogs: float, operating_expenses: float = 0.0) -> dict:
    """See kb/docs/profit_margin_basics.md. operating_expenses is optional (excludes COGS)."""
    if revenue == 0:
        return {"error": "Revenue cannot be zero."}
    gross_profit = revenue - cogs
    gross_margin_pct = (gross_profit / revenue) * 100
    result = {
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": round(gross_margin_pct, 2),
    }
    if operating_expenses:
        operating_profit = gross_profit - operating_expenses
        operating_margin_pct = (operating_profit / revenue) * 100
        result["operating_profit"] = round(operating_profit, 2)
        result["operating_margin_pct"] = round(operating_margin_pct, 2)
    return result


def dso_calculator(accounts_receivable: float, total_credit_sales: float, days_in_period: int = 30) -> dict:
    """Days Sales Outstanding — see kb/docs/invoicing_and_receivables.md."""
    if total_credit_sales == 0:
        return {"error": "Total credit sales cannot be zero."}
    dso = (accounts_receivable / total_credit_sales) * days_in_period
    return {
        "days_sales_outstanding": round(dso, 1),
        "days_in_period_used": days_in_period,
        "formula": "DSO = (Accounts Receivable / Total Credit Sales) * Days in Period",
    }


TOOL_REGISTRY = {
    "emi_calculator": {
        "func": emi_calculator,
        "description": "Calculates monthly EMI for a business loan.",
        "params": "principal (number), annual_rate_pct (number), tenure_years (number)",
    },
    "break_even_point": {
        "func": break_even_point,
        "description": "Calculates the break-even point in units and revenue given fixed costs, selling price, and variable cost per unit.",
        "params": "fixed_costs (number), selling_price_per_unit (number), variable_cost_per_unit (number)",
    },
    "business_cash_reserve_target": {
        "func": business_cash_reserve_target,
        "description": "Calculates target cash reserve given monthly fixed expenses.",
        "params": "monthly_fixed_expenses (number), months_of_cover (integer, optional, default 6)",
    },
    "working_capital_calculator": {
        "func": working_capital_calculator,
        "description": "Calculates working capital given current assets and current liabilities.",
        "params": "current_assets (number), current_liabilities (number)",
    },
    "profit_margin_calculator": {
        "func": profit_margin_calculator,
        "description": "Calculates gross margin (and operating margin if operating expenses given) from revenue and costs.",
        "params": "revenue (number), cogs (number), operating_expenses (number, optional, default 0)",
    },
    "dso_calculator": {
        "func": dso_calculator,
        "description": "Calculates Days Sales Outstanding (DSO) — how long it takes to collect payment on average.",
        "params": "accounts_receivable (number), total_credit_sales (number), days_in_period (integer, optional, default 30)",
    },
}


async def select_tool(question: str, facts_text: str, history_text: str) -> dict:
    """
    Asks the LLM whether the question needs a precise calculation, and if so,
    which tool and with what arguments — extracted from the question, known
    facts, or recent conversation. The LLM only SELECTS the tool and ARGUMENTS;
    it never does the arithmetic itself, avoiding LLM math errors.

    Returns: {"use_tool": bool, "tool_name": str|None, "arguments": dict}
    """
    tool_descriptions = "\n".join(
        f"- {name}: {info['description']} Parameters: {info['params']}"
        for name, info in TOOL_REGISTRY.items()
    )
    system_prompt = (
        "You decide whether a user's business finance question needs a PRECISE "
        "calculation using one of these tools, or whether it's better answered "
        "with general explanation from a knowledge base.\n\n"
        f"Available tools:\n{tool_descriptions}\n\n"
        "Only choose a tool if ALL required numeric arguments are clearly available "
        "from the question, known facts, or recent conversation — never invent or "
        "guess a missing number. If any required argument is missing, respond with "
        "use_tool: false so the assistant can ask the user for it instead of guessing.\n\n"
        "Respond with a JSON object with exactly these keys: "
        '"use_tool" (boolean), "tool_name" (string or null), "arguments" (object, empty if use_tool is false).'
    )
    user_prompt = (
        f"Known business facts: {facts_text}\n\nRecent conversation:\n{history_text}\n\nUser question: {question}"
    )

    result = await chat_completion_json(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    )
    if result.get("_parse_error"):
        return {"use_tool": False, "tool_name": None, "arguments": {}}
    return {
        "use_tool": bool(result.get("use_tool", False)),
        "tool_name": result.get("tool_name"),
        "arguments": result.get("arguments", {}) or {},
    }


def run_tool(tool_name: str, arguments: dict) -> dict | None:
    """Runs the actual Python calculator — this is where the real math happens,
    never the LLM. Returns None if the tool name or arguments are invalid."""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return None
    try:
        return tool["func"](**arguments)
    except (TypeError, ValueError):
        return None


async def synthesize_answer(question: str, kb_context: str, facts_text: str, history_text: str) -> dict:
    """
    Two-step reasoning:
    1. Check if this question needs a precise calculation (EMI, break-even, etc).
       If so, run the REAL Python formula and phrase the answer around it.
    2. Otherwise, fall back to KB-grounded LLM synthesis.

    Returns: {"answer": str, "self_confidence": float, "justification": str, "used_calculator": bool}
    """
    tool_decision = await select_tool(question, facts_text, history_text)

    if tool_decision["use_tool"] and tool_decision["tool_name"]:
        calc_result = run_tool(tool_decision["tool_name"], tool_decision["arguments"])
        if calc_result is not None and "error" not in calc_result:
            return await _phrase_calculation_result(question, tool_decision["tool_name"], calc_result)
        # Tool selection said yes but args/result were invalid — fall through to KB synthesis.

    return await _synthesize_from_kb(question, kb_context, facts_text, history_text)


async def _phrase_calculation_result(question: str, tool_name: str, calc_result: dict) -> dict:
    """Takes the REAL calculated numbers and asks the LLM only to phrase them
    clearly — the LLM cannot alter the numbers, only explain them."""
    system_prompt = (
        "You explain a business finance calculation result to the user in plain "
        "language. The numbers below are EXACT and already correctly calculated — "
        "do not recalculate, alter, or round them differently. Just explain what "
        "they mean clearly and concisely, in 1-3 sentences.\n\n"
        "Respond with a JSON object with exactly these keys: "
        '"answer" (string), "self_confidence" (float 0-1), "justification" (one short sentence).'
    )
    user_prompt = f"User question: {question}\n\nCalculation used: {tool_name}\nExact result: {calc_result}"

    result = await chat_completion_json(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    )
    if result.get("_parse_error"):
        return {
            "answer": f"Result: {calc_result}",
            "self_confidence": 0.9,
            "justification": f"Calculated directly using {tool_name}.",
            "used_calculator": True,
        }
    return {
        "answer": result.get("answer", str(calc_result)),
        "self_confidence": max(0.85, float(result.get("self_confidence", 0.9))),
        "justification": result.get("justification", f"Calculated directly using {tool_name}."),
        "used_calculator": True,
    }


async def _synthesize_from_kb(question: str, kb_context: str, facts_text: str, history_text: str) -> dict:
    system_prompt = (
        "You are the reasoning component of a business finance assistant. "
        "Answer ONLY using the provided KB context and known business facts. "
        "If the KB context does not contain enough information to answer confidently, "
        "say so plainly rather than guessing — do not fabricate numbers, rates, or rules. "
        "Never give specific tax rates, interest rates, or regulatory figures unless they "
        "appear in the KB context. "
        "Respond with a JSON object with exactly these keys: "
        '"answer" (string), "self_confidence" (float 0-1), "justification" (one short sentence).'
    )
    user_prompt = (
        f"Known business facts: {facts_text}\n\n"
        f"Recent conversation:\n{history_text}\n\n"
        f"Retrieved KB context:\n{kb_context or '(no relevant KB content found)'}\n\n"
        f"User question: {question}"
    )

    result = await chat_completion_json(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    )

    if result.get("_parse_error"):
        return {
            "answer": "I'm having trouble forming a confident answer right now.",
            "self_confidence": 0.0,
            "justification": "Model response could not be parsed.",
            "used_calculator": False,
        }

    return {
        "answer": result.get("answer", ""),
        "self_confidence": float(result.get("self_confidence", 0.0)),
        "justification": result.get("justification", ""),
        "used_calculator": False,
    }
