# 🤖 Signal Review Bot

An intelligent advisory system designed to automate the evaluation of trading signals. The bot uses LLMs to interpret unstructured signal data, calculate risk metrics, and provide a standardized "Verdict" to traders.

## 🚀 Core Features
* **LLM Signal Parsing:** Converts irregular text signals into structured data using OpenAI's JSON mode.
* **Automated RR Calculation:** Real-time logic to determine Risk-to-Reward ratios.
* **Intelligent Verdict System:** Categorizes trades (e.g., GOOD, SUPER, MASSIVE) based on mathematical conviction.
* **Persona-Driven Advice:** Context-aware prompts that act as a disciplined financial advisor.

## 🛠️ Technical Stack
* **Backend:** Python (FastAPI), LangChain, OpenAI API.
* **Frontend:** React.js / Vite.
* **Data Handling:** Pydantic for schema validation.

## 🏗️ Architecture Note
The system follows a decoupled architecture where the LLM is treated as a logic engine. Prompt engineering is focused on **deterministic output**, ensuring that the mathematical analysis remains consistent while the advisory tone remains professional.

---

The model utilizes a leaf-wise growth strategy to capture volatility in the PSX. Feature engineering focused on momentum indicators and volume-weighted price action to maximize the model's precision in "Buy" signal conviction.
