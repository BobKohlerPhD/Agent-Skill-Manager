---
name: demo-skill
description: A skill to demonstrate how the manager works
---
# Skill: Demo Skill

## Trigger Criteria & Bounds
*   **Use Cases**: Demonstrating how the manager works.
*   **Anti-Patterns (Do NOT Use)**: Do not use for real tasks; only for demonstration.

## Execution Protocol
*   **Pre-conditions**: No specific workspace states required.
*   **Step-by-Step Instructions**:
    1. Run validation step 1.
    2. Run validation step 2.
*   **Error Handling**: If a test step fails, output a warning and proceed with logging.

## Requirements & Environment
*   **System Dependencies**: None.
*   **Runtime Packages**: None.
*   **API Keys / Environment Variables**: None.

## Few-Shot Cognitive Examples
### Example 1: Basic Demo
*   **Input**:
    ```json
    { "action": "test" }
    ```
*   **Agent Thought (CoT)**: The user wants to run a demo action. I will log a success message.
*   **Action**: `echo "Demo success"`
*   **Output**:
    ```json
    { "status": "success" }
    ```
