import logging
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from src.models import AgentInput
from src.agents.multi_agent_crew import run_aml_crew

r = run_aml_crew(AgentInput(
    wallet_address="0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
    qubo_risk_score=0.92,
    qubo_flagged_nodes=[],
    trace_id=str(uuid.uuid4()),
))

print(f"Risk: {r.risk_level} | Action: {r.recommended_action} | F-beta: {r.f_beta_score}")
