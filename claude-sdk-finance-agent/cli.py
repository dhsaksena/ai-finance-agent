import logging
from anthropic import Anthropic
from ingest import load_notes
from search import TOOLS, get_stock_fundamentals, get_company_research, search_ticker
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic()


def build_context(notes):
    """Turn the list of notes into one labeled block of text."""
    parts = []
    for note in notes:
        parts.append(f"## {note['filename']}\n{note['content']}")
    return "\n\n".join(parts)


def ask_advisor(history, context):
    """Send the conversation so far. Loop while Claude wants to use a tool."""
    while True:
        try:
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=2000,
                system=(
                    "You are a stock analyst. Your ONLY job right now is to give "
                    "a buy, hold, or sell judgment on a specific stock, based on "
                    "its own financial statistics — valuation, profitability, "
                    "growth, and price trend. Do NOT reason about how it fits "
                    "the user's overall portfolio or diversification; that is "
                    "out of scope for now.\n\n"
                    "Never guess a stock ticker — always call search_ticker "
                    "first to confirm it, and if it isn't found, ask the user "
                    "for it directly. Then call get_stock_fundamentals to get "
                    "real numbers.\n\n"
                    "If the fundamentals alone leave a real gap in your "
                    "confidence (a distorted ratio, missing balance sheet "
                    "fields, unclear cause for a number), call "
                    "get_company_research next to check for saved human notes "
                    "on this ticker BEFORE asking the user. Only ask the user "
                    "directly if get_company_research has nothing relevant "
                    "either.\n\n"
                    f"{context}"
                ),
                messages=history,
                tools=TOOLS,
            )
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return f"Error: Unable to reach the API. {str(e)}"

        # Record Claude's turn (whether it's a final answer or a tool request).
        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    return block.text
            logger.warning("No text block found in response")
            return "No response generated."

        # Claude asked for one or more tool calls — execute each, collect results.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                logger.info(
                    "Tool call: name=%s, tool_use_id=%s, input=%s",
                    block.name,
                    block.id,
                    block.input,
                )
                try:
                    if block.name == "search_ticker":
                        result = search_ticker(**block.input)
                    elif block.name == "get_stock_fundamentals":
                        result = get_stock_fundamentals(**block.input)
                    elif block.name == "get_company_research":
                        result = get_company_research(**block.input)
                    else:
                        result = {"error": f"Unknown tool: {block.name}"}
                except Exception as e:
                    logger.error(f"Tool execution failed for {block.name}: {e}")
                    result = {"error": f"Tool failed: {str(e)}"}

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )

        # Hand the results back as the next "user" turn, then loop to call again.
        history.append({"role": "user", "content": tool_results})


def main():
    notes = load_notes()
    context = build_context(notes)
    history = []

    print("Finance Agent ready. Ask a question (or 'exit' to quit).\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break

        history.append({"role": "user", "content": question})
        answer = ask_advisor(history, context)

        print(f"\nAdvisor: {answer}\n")


if __name__ == "__main__":
    main()