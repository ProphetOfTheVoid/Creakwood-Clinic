#!/usr/bin/env python
import sys, os, yaml, warnings, random, textwrap, traceback
from litellm import completion
from medic.flow import MedicFlow, ConversationalState

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def check_ollama_connection():
    try:
        response = completion(
            model="ollama/llama3.1:latest",
            messages=[{"role":"user", "content":"test"}],
            api_base="http://localhost:11434"
        )

        print("✅ Ollama successfully connected")
        return True
    except Exception as e:
        print(f"❌ Error while attempting to connect with Ollama: {e}")
        print("⚠️  Fallback to LiteLLM")
    return False

def load_config_from_yaml(filepath: str) -> dict:
    abs_filepath = os.path.join(os.path.dirname(__file__), filepath)
    
    if not os.path.exists(abs_filepath):
        print(f"🔴 FATAL ERROR: missing config file {abs_filepath}")
        sys.exit(1)
        
    try:
        with open(abs_filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except Exception as e:
        print(f"🔴 ERROR while loading file YAML {abs_filepath}: {e}")
        sys.exit(1)

def authentication_wrapper() -> dict:
    print("🥊: Halt it user! The operation you require can't be executed by a non-verified user!")
    print("🥊: Authentication procedure initiated. Please, provide your full name and surname.")
    full_name = input("✒️: ")
    print("🥊: Provide your date of birth in MM/DD/YYYY format")
    date = input("✒️: ")

    buffer = ""
    for x in range (0, 6):
        num = random.randint(0, 9)
        buffer += str(num)

        try:         
            with open('knowledge/user_devices/phone.txt', 'w') as f:
                f.write(f"===TOKEN===\n{buffer}")
        except Exception as e:
            print(f"🔴 Failed to write appointment: {e}")

    print("🥊: A one-time token has been sent to you through a notification on your mobile device. Provide said token.")
    token = input("✒️: ")

    if token == buffer:
        output = {"full name": full_name, "date": date}
    else:
        output = {"full name": "ERROR", "date": "ERROR"}
    return output

def booking_wrapper():
    print("⌚: Booking procedure initiated. Please, provide the desired date (in MM/DD/YYYY format):")
    desired_date = input("✒️: ")
    print("⌚: Provide the desired time (in AM/PM format) - Remind yourself that the avaible time slots are:")
    print([ "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM"])
    desired_time = input("✒️: ")

    output = {"desired_date": desired_date, "desired_time": desired_time}
    return output

def cancel_wrapper():
    print("⌚❌: Cancel booking procedure initiated. Please, provide the date of your appointment (in MM/DD/YYYY format):")
    appointment_date = input("✒️: ")
    print("⌚❌: Select the time your appointment is scheduled at. The avaible time slots are:")
    print([ "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM"])
    appointment_time = input("✒️: ")

    output = {"appointment_date": appointment_date, "appointment_time": appointment_time}
    return output

AGENTS_CONFIG_PATH = 'config/agents.yaml'
TASKS_CONFIG_PATH = 'config/tasks.yaml'

def kickoff():
    agents_config = load_config_from_yaml(AGENTS_CONFIG_PATH)
    tasks_config = load_config_from_yaml(TASKS_CONFIG_PATH)
    
    check_ollama_connection()

    persistent_state = ConversationalState()

    welcome_text = """
    === Secure Medical Assistant ===

    Welcome to our Virtual Medic Practice! I'm here to help you with:
    - Scheduling and managing appointments
    - General office information and hours
    - Non-medical inquiries about our practice
    - Downloading your medical record

    ⚠️ Please, note Patient's privacy is our highest priority. Any request involving personal medical information, appointment details or lab results will require identity verification ⚠️
    """

    print(textwrap.dedent(welcome_text))

    gather_identity_flag = False
    gather_booking_details_flag = False
    gather_cancel_details_flag = False
    finish = False
    try:
        while not finish:

            if(gather_identity_flag):
                payload = authentication_wrapper()

                if "ERROR" not in payload.get('full name') and "ERROR" not in payload.get('date'):
                    persistent_state.payload = payload
                    persistent_state.user_auth_attempt = True
                    gather_identity_flag = False
                else:
                    print("⚕️: The provided token doesn't match. Please, try again.")
                    continue
            elif gather_booking_details_flag:
                persistent_state.payload = booking_wrapper()
                persistent_state.user_book_attempt = True
                gather_booking_details_flag = False
            elif gather_cancel_details_flag:
                persistent_state.payload = cancel_wrapper()
                persistent_state.user_cancel_attempt = True
                gather_cancel_details_flag = False
            else:
                print(f"⚕️: Welcome back {persistent_state.user_identity.get('full name') or ""}! How may I assist you today? (Type 'exit' to quit or 'logout' to logout)")
                user_input = input("✒️: ")

                if user_input.lower() in ["logout"]:
                    print("⚕️: Logging out!")
                    persistent_state.user_identity.clear()
                    persistent_state.user_verified = False
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    print("⚕️: Goodbye!")
                    finish=True
                    continue

                persistent_state.messages.append({"role":"user", "content": user_input})
            
            # Launching the flow
            medic_flow = MedicFlow(
                agents_config=agents_config,
                tasks_config=tasks_config,
                state=persistent_state
            )
            medic_flow.kickoff()
            

            reply = persistent_state.messages[-1].get('content')

            # Checks for authentication-related flags
            if("authentification procedure" in reply):
                gather_identity_flag = True
            elif("identity_unverified" in reply):
                persistent_state.user_auth_attempt = False

                logging_result = f"User authentication FAILED as {persistent_state.user_identity.get('full name')} born in {persistent_state.user_identity.get('date')}"
                persistent_state.messages.append({"role": "assistant", "content": logging_result})

                if isinstance(reply, str):
                    print(f"⚕️: ⛔Authentication failed. Returning to neutral state.⛔\n")
                continue
            elif("identity_verified" in reply):
                persistent_state.user_auth_attempt = False
                persistent_state.user_verified = True
                persistent_state.user_identity = persistent_state.payload
                persistent_state.payload = ""

                logging_result = f"User authentication SUCCESSFUL as {persistent_state.user_identity.get('full name')} born in {persistent_state.user_identity.get('date')}"
                persistent_state.messages.append({"role": "assistant", "content": logging_result})

                if isinstance(reply, str):
                    print(f"⚕️: ✅Authentication success. Redirecting...✅\n")
                continue
            

            # Checks for booking-related flags
            if("appointment booking procedure" in reply):
                gather_booking_details_flag = True
            elif "not available" in reply:
                gather_booking_details_flag = True
                persistent_state.user_book_attempt = False
                persistent_state.payload = ""
            elif("successfully booked your appointment" in reply or "error while booking your appointment" in reply):
                persistent_state.user_book_attempt = False
                persistent_state.payload = ""


            # Checks for cancel-booking-related flags
            if("appointment cancelling procedure" in reply):
                gather_cancel_details_flag = True
            elif "couldn't find any appointment in your name" in reply:
                gather_cancel_details_flag = True
                persistent_state.user_cancel_attempt = False
                persistent_state.payload = ""
            elif("successfully cancelled your appointment" in reply or "error while cancelling your appointment" in reply):
                persistent_state.user_cancel_attempt = False
                persistent_state.payload = ""

            # At the end, print output
            if isinstance(reply, str):
                print(f"⚕️: {reply}\n")

    except TypeError as e:
        print(f"🔴 Error in flow constructor: {e}")
    except Exception as e:
        print(f"🔴 Unexpected error: {e}")
        traceback.print_exc()

#def plot():
#    check_ollama_connection()
#    medic_flow = MedicFlow()
#    medic_flow.plot()


#def run():
#    check_ollama_connection()
#    MedicFlow().kickoff()


if __name__ == "__main__":
    kickoff()
