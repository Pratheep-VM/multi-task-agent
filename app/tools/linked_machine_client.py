import os
from pathlib import Path

from mudraid import MachineAgent, MachineIdentity, PyJWTSigner, RequestedScopes


def build_agent(prefix="MUDRAID"):
    """Load this client's explicit configuration; never fall back to legacy keys."""

    def required(name):
        key = f"{prefix}_{name}"
        value = os.environ.get(key, "").strip()
        if not value:
            raise ValueError(f"Set {key} for the V2 machine client")
        return value

    return MachineAgent(
        MachineIdentity(
            client_id=required("CLIENT_ID"),
            token_endpoint=required("TOKEN_ENDPOINT"),
            audience=required("ASSERTION_AUDIENCE"),
            resource=required("RESOURCE"),
            scopes=RequestedScopes.of(required("SCOPES").split()),
            signer=PyJWTSigner(
                Path(required("PRIVATE_KEY_PATH")).read_bytes(),
                kid=required("KEY_ID"),
            ),
        )
    )


if __name__ == "__main__":
    agent = build_agent()
    try:
        response = agent.get(os.environ["MUDRAID_TASKS_URL"], timeout=15)
        response.raise_for_status()
        print(f"Platform call succeeded: HTTP {response.status_code}")
    finally:
        agent.close()