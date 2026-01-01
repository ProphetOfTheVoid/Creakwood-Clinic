# 🤖 AI Medical Assistant ⚕️
This is a simulation for a wider-scoped academic project aiming to evaluate the robustness of Artificial Intelligence within a simulated security-critical environment (see [.pfd](https://github.com/ProphetOfTheVoid/Creakwood-Clinic/blob/main/Medical%20Assistant.pdf) file). For further reference about the entire project, check out the following slideshow:
* https://www.canva.com/design/DAG8-4DB5xQ/DYqXfU53T4-cPlUgTnO06A/view?utm_content=DAG8-4DB5xQ&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hf43addf8d8

The chosen scenario is a medical practice, Creakwood Clinic, supported by an AI-driven Medical Assistant. The latter assists patients connecting to the platform by answering their questions and guiding them in step-by-step procedures, much like any human secretary would. The system is governed by a single non-negotiable rule: the protection of the patients’ privacy.

The project is based on the CrewAI framework: https://github.com/crewAIInc/crewAI 

## The simulation 🖼️
The simulated platform offers three primary services:
* Appointment management (booking and cancellation)
* Consultation of personal medical records 
* Answers to non-confidential questions (e.g. address, clinic hours, staff availability)

The first two services are classified as sensitive operations and require successful identity verification. If the user refuses to provide identification or fails the identification procedure, the operation is terminated. Once the user it’s authenticated, the system will proactively engage with the user to gather the necessary information to complete the requested procedure (e.g. the date of the appointment, the section of the medical record, …).

The Medical Assistant interacts with a mock-DB composed of a set of text files. These databases are divided into:
* Public files, containing non-sensitive information:
  * `medic/knowledge/clinic_public_info.txt`
* Private files, assumed to be accessible only by authorised roles:
  * `medic/knowledge/clinic_appointments.txt`
  * `medic/knowledge/clinic_DB.txt`
  * `medic/knowledge/user_devices/*`
The contents of those files are plain (i.e. not encrypted) to maintain a high throughput. In a real-world deployment, sensitive information should be kept secret even while stored.

User interaction occurs via **standard input** (`stdin`), simulating a basic conversational interface.

## Execution outline 🔨
Iteratively, the `main` function creates a `MedicFlow` object, provides it with the necessary information about the conversation so far (stored within `ConversationalState`) and launches it. After the Flow execution is complete, the output is gathered through the same `ConversationalState`, which effectively bridges between the Flow and the function, and `gather_*` flags are raised, influencing the main execution logic. Similarly, flags are contained within `ConversationalState` too: they're raised in `main` and influence the Flow execution logic.

The structure is therefore the following. The main function is in the first pseudo-code, and the flow execution is in the latter. All steps written in **purple** are executed by an AI agent:
![Diagram](mainloop.png)

![Diagram](innerloop.png)

## The LLM and the Agents ⚙️
The system uses the latest version of Llama 3.1, executed locally through Ollama without altering its default hyperparameters. Hence, Ollama and the correct Llama model must be running in the background at all times for the project to work effectively.
CrewAI's fallback procedure in case the Llama model isn't found defaults to LiteLLM, which can be installed as a library by the `uv` package manager (see within the project for further README or CrewAI documentation).

The agent definitions as well as their tasks can be found in the YAML configuration files. Despite the prompt conditioning implemented, the Agents still behave in a non-deterministic way at times. Presumably, it's either due to the limited expressive baseline of the chosen LLMs or too wide a scope given to the Agents.

No crews are used. Although executing Crews within Flows is possible, said Crews would be composed of 1 agent in this scenario. Hence, the desired Agent is directly launched when needed.

## Project Structure Overview 📂
- `pyproject.toml` contains everything about the installed dependencies and the functions which every keyword in commands like `crewai run` triggers
- `knowledge` contains all text files used
  - `clinic_DB` is assumed private and contains confidential info, like credentials and medical records
  - `clinic_appointments` is assumed to be private and contains the scheduled appointments. It is edited after the appointment management procedures
  - `public_info` contains the info the system uses when the user queries a non-sensitive question. It's a source of knowledge derived from all potentially confidential details.
  - `users_devices` contains both the `email` where the medical results are sent and the `smartphone` in which the 2FA token is received
- `src/medic` contains the actual code:
  - `main.py` contains main and input gathering functions
  - `flow.py` contains the flow execution, as well as the Agents-summoning functions 


## ⌨️ Launch and interaction step-by-step:
Everything is printed on the _System.out_ for the user to see (no graphic interface). 

Before beginning, you must have your own `.env` file, which is omitted in this repo because it contains personal data. It should be stored in the `medic` folder and, assuming you want the same `Ollama` config, contain the following lines (11434 is the default Ollama port):
`MODEL=ollama/llama3.1:latest
API_BASE=http://localhost:11434`

If you wish to use Gemini, Claude or OpenAI's API keys, the `.env` file must contain different info. Read more about it in CrewAI's documentation.

1. Position yourself in the `medic` folder
2. Make sure the correct `Llama` model is running (or after having successfully switched to an API-based alternative), and then the correct packages are installed through the `uv` packet manager
3. Run `crewai run` to begin the execution → If you're still using `Ollama`, you should be notified of whether connecting to it has been successful 
4. Remind yourself that, at any time, execution can be stopped with `^C`
5. You're now free to interact with the Medical Assistant. Try requesting an operation (e.g. "I wanna book an appointment" or "Will you show me the latest result of my cardiac stress test?") or ask a general non-sensitive question (e.g. "Is the clinic open on Fridays?"). For the best performance, try not to be vague or the AI may mis-categorise your request.
6. Depending on your request, you might have to authenticate. If that happens, provide the required credentials (can be found in the  `medic/knowledge/clinic_DB.txt`) and the 2FA token, found in `medic/knowledge/user_devices/phone.txt`
7. If you have completed the authentication procedure and requested to see a medical record, it will be available in  `medic/knowledge/user_devices/email.txt`

## 🛑 Technical issues experienced and not solved
1. The flow execution is too verbose. Yet, it's not possible to instruct CrewAI's flow to print less or no output.
2. The loop had to be decoupled from within CrewAI's flow and now sits in `main`. That's because Flow objects have a `maximum_depth` which, when reached, terminates the execution.
3. The handling of complex `@router` functions within the Flows is messy. If RouterA returns the keyword functionB is listening to, the latter executes in a loop, forcing the need for an additional third step before the flow execution can conclude. This is linked to the fact that returning a keyword within "..." enables it until the flow execution is terminated (i.e. when functionB executes, the keyword that triggered said execution isn't cleared and remains active, creating a loop).
