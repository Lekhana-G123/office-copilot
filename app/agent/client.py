import json
import re

from openai import OpenAI
from sqlalchemy.orm import Session

from app.agent.prompts import build_system_prompt
from app.agent.runner import run_tool
from app.agent.tool_schema import TOOLS
from app.config import settings
from app.models import User
from app.quick_commands import try_quick_command


def _assistant_message_for_api(message) -> dict:
    """Groq only accepts role, content, tool_calls — strip extra OpenAI fields."""
    msg: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return msg


def run_agent(db: Session, user_message: str, current_user: User) -> dict:
    requester_name = current_user.name

    quick = try_quick_command(db, current_user, user_message)
    if quick:
        return quick

    if not settings.groq_api_key:
        return {
            "reply": "Groq API key is missing. Add GROQ_API_KEY to your .env file.",
            "tool_calls": [],
        }

    client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {
            "role": "user",
            "content": f"[Logged in as: {requester_name}]\n\n{user_message}",
        },
    ]

    tool_calls_made = []
    max_turns = 6

    for _ in range(max_turns):
        try:
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            err = str(e)
            if "tool_use_failed" in err or "assign_task" in err:
                return {
                    "reply": (
                        "I had trouble with that AI tool call. Try one of these exact commands:\n"
                        "- show my tasks\n"
                        "- show team status\n"
                        "- assign task Prepare test data to You (Intern) due tomorrow\n"
                        "- list rooms\n"
                        "- book room A for 3-7pm\n"
                        "- is intern available today\n"
                        "- is director coming tomorrow\n"
                        "- is Director Kumar available tomorrow"
                    ),
                    "tool_calls": tool_calls_made,
                }
            raise

        choice = response.choices[0]
        assistant_message = choice.message

        if assistant_message.tool_calls:
            messages.append(_assistant_message_for_api(assistant_message))

            for tool_call in assistant_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                if fn_name in (
                    "check_availability",
                    "create_meeting_request",
                    "draft_meeting_email",
                    "book_room",
                    "get_my_tasks",
                    "get_team_status",
                    "assign_task",
                ):
                    if fn_name == "book_room":
                        fn_args.setdefault("booker_name", requester_name)
                    elif fn_name == "check_availability":
                        fn_args.setdefault("requester_name", requester_name)
                    elif fn_name == "get_my_tasks":
                        fn_args.setdefault("requester_name", requester_name)
                    elif fn_name in ("get_team_status", "assign_task"):
                        fn_args.setdefault("manager_name", requester_name)
                    else:
                        fn_args.setdefault("requester_name", requester_name)

                result = run_tool(db, fn_name, fn_args)
                tool_calls_made.append({"tool": fn_name, "args": fn_args, "result": result})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })
            continue

        reply = assistant_message.content or ""
        if (
            re.search(r"\bbook\b", user_message, re.I)
            and re.search(r"\b(booked|confirmed|reserved)\b", reply, re.I)
            and not any(t.get("tool") == "book_room" for t in tool_calls_made)
        ):
            return {
                "reply": (
                    "I couldn't confirm that booking in the system. "
                    "Try: book room A for 3-7pm"
                ),
                "tool_calls": tool_calls_made,
            }

        return {
            "reply": reply,
            "tool_calls": tool_calls_made,
        }

    return {
        "reply": "I need more steps to complete that request. Please try a simpler question.",
        "tool_calls": tool_calls_made,
    }
