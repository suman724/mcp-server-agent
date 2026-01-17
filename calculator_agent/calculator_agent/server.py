
import logging

import uvicorn

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps.jsonrpc import A2AFastAPIApplication
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers.default_request_handler import (
    DefaultRequestHandler,
)
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    InvalidParamsError,
    Message,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TransportProtocol,
    UnsupportedOperationError,
)
from a2a.utils import get_message_text, get_text_parts, new_agent_text_message
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from a2a.utils.errors import ServerError

from .agent import AgentError, CalculatorAgent
from .config import A2A_BASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("calculator_server")

AGENT_PATH = "/calculator"


def _build_agent_card(base_url: str) -> AgentCard:
    base = base_url.rstrip("/")
    agent_url = base if base.endswith(AGENT_PATH) else f"{base}{AGENT_PATH}"
    return AgentCard(
        name="Calculator Agent",
        description=(
            "An intelligent agent that performs mathematical operations using "
            "an MCP calculator server."
        ),
        url=agent_url,
        version="0.1.0",
        preferred_transport=TransportProtocol.jsonrpc.value,
        additional_interfaces=[
            AgentInterface(url=agent_url, transport=TransportProtocol.jsonrpc.value)
        ],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
            state_transition_history=False,
        ),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="calculator",
                name="Calculator",
                description="Handles basic arithmetic by calling MCP calculator tools.",
                tags=["math", "calculator"],
                examples=[
                    "Calculate 5 + 3",
                    "What is the product of 9 and 12?",
                ],
            )
        ],
    )


def _validate_message(message: Message) -> None:
    if message.role != Role.user:
        raise ServerError(
            InvalidParamsError(message="Message role must be 'user'.")
        )
    text_parts = get_text_parts(message.parts)
    combined = "".join(text_parts).strip()
    if not text_parts or not combined:
        raise ServerError(
            InvalidParamsError(
                message="Message must include at least one non-empty text part."
            )
        )


def _build_prompt(context: RequestContext) -> str:
    history: list[Message] = []
    if context.current_task and context.current_task.history:
        history = list(context.current_task.history)
    elif context.message:
        history = [context.message]

    if context.configuration and context.configuration.history_length:
        history = history[-context.configuration.history_length :]

    lines = []
    for msg in history:
        text = get_message_text(msg).strip()
        if not text:
            continue
        role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        lines.append(f"{role}: {text}")
    return "\n".join(lines).strip()


class CalculatorAgentExecutor(AgentExecutor):
    def __init__(self, agent: CalculatorAgent):
        self._agent = agent

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        task_id = (
            context.task_id
            or (context.current_task.id if context.current_task else None)
        )
        context_id = (
            context.context_id
            or (context.current_task.context_id if context.current_task else None)
        )
        if not task_id or not context_id:
            logger.error("Missing task_id or context_id in request context.")
            return

        prompt = _build_prompt(context)
        if not prompt:
            response_text = "Message must include at least one non-empty text part."
            status_state = TaskState.rejected
        else:
            try:
                response_text = await self._agent.run(prompt)
                status_state = TaskState.completed
            except AgentError as exc:
                logger.error("Agent execution error: %s", exc)
                response_text = f"Agent error: {exc}"
                status_state = TaskState.failed
            except Exception as exc:
                logger.exception("Unexpected error during agent execution")
                response_text = f"Internal error: {exc}"
                status_state = TaskState.failed

        response_message = new_agent_text_message(
            response_text,
            context_id=context_id,
            task_id=task_id,
        )

        history: list[Message] = []
        if context.current_task and context.current_task.history:
            history = list(context.current_task.history)
        elif context.message:
            history = [context.message]
        history.append(response_message)

        task = Task(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(state=status_state, message=response_message),
            history=history,
        )
        await event_queue.enqueue_event(task)

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        task_id = (
            context.task_id
            or (context.current_task.id if context.current_task else None)
        )
        context_id = (
            context.context_id
            or (context.current_task.context_id if context.current_task else None)
        )
        if not task_id or not context_id:
            logger.error("Missing task_id or context_id in cancel request.")
            return
        response_message = new_agent_text_message(
            "Task canceled.",
            context_id=context_id,
            task_id=task_id,
        )

        history: list[Message] = []
        if context.current_task and context.current_task.history:
            history = list(context.current_task.history)
        history.append(response_message)

        task = Task(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(state=TaskState.canceled, message=response_message),
            history=history,
        )
        await event_queue.enqueue_event(task)


class CalculatorRequestHandler(DefaultRequestHandler):
    async def on_message_send(self, params, context=None):
        _validate_message(params.message)
        return await super().on_message_send(params, context)

    async def on_resubscribe_to_task(self, params, context=None):
        raise ServerError(UnsupportedOperationError())


agent_instance = CalculatorAgent()
agent_card = _build_agent_card(A2A_BASE_URL)
executor = CalculatorAgentExecutor(agent_instance)
request_handler = CalculatorRequestHandler(
    agent_executor=executor,
    task_store=InMemoryTaskStore(),
)

a2a_app = A2AFastAPIApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

app = a2a_app.build(
    title="Calculator Agent A2A",
    description="Exposes the Calculator Agent via A2A JSON-RPC protocol.",
    agent_card_url=AGENT_CARD_WELL_KNOWN_PATH,
    rpc_url=AGENT_PATH,
)


@app.get("/calculator/info", response_model=AgentCard)
async def get_agent_card_alias() -> AgentCard:
    return agent_card


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def start():
    """Entry point for running the server programmatically."""
    uvicorn.run(
        "calculator_agent.server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    start()
