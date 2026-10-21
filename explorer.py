import logging

log = logging.getLogger("axiom.explorer")

class WorkspaceExplorer:
    def __init__(self, llm):
        self.llm = llm

    def deduce_test_target(self, prompt: str, available_tests: list) -> str:
        """Uses the local 3B model to intelligently guess the correct test file."""
        if not available_tests:
            return None
        if len(available_tests) == 1:
            return available_tests[0]

        query = f"""
        You are a repository routing agent.
        USER PROMPT: "{prompt}"
        AVAILABLE TEST FILES:
        {chr(10).join(available_tests)}

        Return ONLY the exact file path from the list above that best matches the user's prompt. Do not add markdown or explanations.
        """
        try:
            # Use local model for fast, zero-cost routing
            ans = self.llm.get_local_response(query, agent_role="Triage_Router").strip()
            for test_file in available_tests:
                if test_file in ans:
                    return test_file
        except Exception as e:
            log.warning(f"Explorer fallback failed: {e}")

        # Ultimate fallback if the local model fails
        return available_tests[0]
