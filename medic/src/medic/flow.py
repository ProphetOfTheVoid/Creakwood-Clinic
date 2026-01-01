from crewai.flow.flow import Flow, listen, start, router, or_
from crewai import Agent
from pydantic import BaseModel
from typing import List
import sys, textwrap

import os
os.system('') 
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'

# Functions employing ai agents

async def get_generic_reply(agent_config: dict, task_config: dict, conversation_context: str, file_path: str) -> str:
    if not os.path.exists(file_path):
        print(f"🔴 Error: clinic public info file not found at path {file_path}")
        return "Internal Error"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        print(f"🔴 Error while reading file: {e}")
        return "Internal Error"
    
    general_helper = Agent(
        config = agent_config,
        verbose = False
    )

    description = task_config.get('description')
    expected_output = task_config.get('expected_output')

    general_query = f"""
    --TASK INSTUCTIONS--
    {description}

    --INPUT DATA FROM PUBLIC FILE--
    {file_content}
    
    --EXPECTED OUTPUT--
    {expected_output}
    
    --CONVERSATION CONTEXT--
    {conversation_context}
    """

    #print(general_query)

    result = await general_helper.kickoff_async(
        textwrap.dedent(general_query)
    )
    return str(result).strip().lower()

async def get_intent(agent_config: dict, task_config: dict, conversation_context: list) -> str:
    
    intent_analyst = Agent(
        config = agent_config,
        verbose = False
    )

    description = task_config.get('description')
    expected_output = task_config.get('expected_output')
    
    classification_query = f"""
    --TASK INSTUCTIONS--
    {description}

    --EXPECTED OUTPUT--
    {expected_output}
    
    --USER'S QUERY--
    {conversation_context[-1].get('content')}
    """

    # debug
    #print(classification_query)

    result = await intent_analyst.kickoff_async(
        textwrap.dedent(classification_query)
    )
    return str(result).strip().lower()

async def check_identity(agent_config: dict, task_config: dict, payload: dict, file_path: str) -> str:
    if not os.path.exists(file_path):
        print(f"🔴 Error: clinic DB info file not found at path {file_path}")
        return "Internal Error"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        print(f"🔴 Error while reading file: {e}")
        return "Internal Error"
    
    general_helper = Agent(
        config = agent_config,
        verbose = False
    )

    description = task_config.get('description')
    expected_output = task_config.get('expected_output')

    general_query = f"""
    --TASK INSTUCTIONS--
    {description}

    --INPUT DATA FROM PRIVATE DB FILE--
    {file_content}
    
    --INFORMATION PROVIDED BY THE USER--
    {payload}

    --EXPECTED OUTPUT--
    {expected_output}
    """

    #print(general_query)

    result = await general_helper.kickoff_async(
        textwrap.dedent(general_query)
    )
    return str(result).strip().lower()

async def get_operation(agent_config: dict, task_config: dict, conversation_context: list) -> str:
    intent_analyst = Agent(
        config = agent_config,
        verbose = False
    )


    description = task_config.get('description')
    expected_output = task_config.get('expected_output')
    
    classification_query = f"""
    --TASK INSTUCTIONS--
    {description}

    --EXPECTED OUTPUT--
    {expected_output}
    
    --CONVERSATION CONTEXT--
    {conversation_context[-1].get('content')}
    """

    # debug
    # print(classification_query)

    result = await intent_analyst.kickoff_async(
        textwrap.dedent(classification_query)
    )
    return str(result).strip().lower()

async def get_record(agent_config: dict, task_config: dict, conversation_context: str, user_identity: dict, file_path: str) -> str:
    if not os.path.exists(file_path):
        print(f"🔴 Error: clinic DB info file not found at path {file_path}")
        return "Internal Error"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        print(f"🔴 Error while reading file: {e}")
        return "Internal Error"
    
    general_helper = Agent(
        config = agent_config,
        verbose = False
    )

    description = task_config.get('description')
    expected_output = task_config.get('expected_output')

    general_query = f"""
    --TASK INSTUCTIONS--
    {description}

    --INPUT DATA FROM PRIVATE DB FILE--
    {file_content}

    --USER IDENTITY--
    {user_identity}

    --EXPECTED OUTPUT--
    {expected_output}
    
    --CONVERSATION CONTEXT--
    {conversation_context[-1].get('content')}
    """

    #print(general_query)

    result = await general_helper.kickoff_async(
        textwrap.dedent(general_query)
    )
    return str(result).strip().lower()

async def filter_output(prev_reply: str, agent_config: dict, task_config: dict):
    fulter_agent = Agent(
        config = agent_config,
        verbose = False
    )

    description = task_config.get('description')
    expected_output = task_config.get('expected_output')
    
    query = f"""
    --TASK INSTUCTIONS--
    {description}

    --EXPECTED OUTPUT--
    {expected_output}
    
    --OUTPUT TO SANITAIZE--
    {prev_reply}
    """

    # debug
    print(query)

    result = await fulter_agent.kickoff_async(
        textwrap.dedent(query)
    )
    return str(result).strip().lower()


# Utils functions

def get_patient_id(patient_name: str, patient_dob: str) -> str:
    try:    
        with open('knowledge/clinic_DB.txt', 'r') as f:
            content = f.read()
            
        records = content.split('---PATIENT RECORD START---')
            
        for record in records:
            if 'PATIENT RECORD END' not in record:
                continue
            
            # Check if name and DOB match
            if f"FULL_NAME: {patient_name}" in record and f"DATE_OF_BIRTH: {patient_dob}" in record:
                # Extract patient ID
                for line in record.split('\n'):
                    if line.startswith('PATIENT_ID:'):
                        return line.split('PATIENT_ID:')[1].strip()
            
    except Exception as e:
        print(f"🔴 Failed to read patient database: {e}")
        return None

def find_appointment(date: str, time: str, patient_name: str, patient_dob: str, patient_id: str) -> bool:
    if time not in [ "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM"]:
        return False
    
    try:
        with open('knowledge/clinic_appointments.txt', 'r') as f:
            content = f.read()
        
        # Parse all active appointments
        appointments = content.split('---APPOINTMENT RECORD START---')
        
        for appointment in appointments:
            if 'APPOINTMENT RECORD END' not in appointment:
                continue
            
            if f"DATE: {date}" in appointment and f"TIME: {time}" in appointment:
                if f"PATIENT_ID: {patient_id}" in appointment and f"PATIENT_NAME: {patient_name}" in appointment and f"PATIENT_DOB: {patient_dob}" in appointment:
                    return True
               
        return False
        
    except Exception as e:
        print(f"🔴 Failed to find desired appointment: {e}")
        return False

def check_appointment(date: str, time: str) -> bool:

    if time not in [ "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM"]:
        return False
        
    try:
        with open('knowledge/clinic_appointments.txt', 'r') as f:
            content = f.read()
        
        # Parse all active appointments
        appointments = content.split('---APPOINTMENT RECORD START---')
        
        for appointment in appointments:
            if 'APPOINTMENT RECORD END' not in appointment:
                continue
            
            if f"DATE: {date}" in appointment and f"TIME: {time}" in appointment:
                return False
               
        return True
        
    except Exception as e:
        print(f"🔴 Failed to check slot availability: {e}")
        return False

def write_appointment(patient_id: str, patient_name: str, patient_dob: str, date: str, time: str) -> bool:
    try:        
        new_appointment = textwrap.dedent(f"""
        ---APPOINTMENT RECORD START---
        PATIENT_ID: {patient_id}
        PATIENT_NAME: {patient_name}
        PATIENT_DOB: {patient_dob}

        DATE: {date}
        TIME: {time}
        ---APPOINTMENT RECORD END---
        """)
        
        with open('knowledge/clinic_appointments.txt', 'r') as f:
            content = f.read()
 
        end_marker = 'END OF APPOINTMENTS DATABASE'
        end_marker = '========================================\nEND OF APPOINTMENTS DATABASE'
        end_marker_pos = content.find(end_marker)-1
        updated_content = content[:end_marker_pos] + new_appointment + "\n" + content[end_marker_pos:]
        
        with open('knowledge/clinic_appointments.txt', 'w') as f:
            f.write(updated_content)

        print(f"✅ Appointment written to file")
        return True
        
    except Exception as e:
        print(f"🔴 Failed to write appointment: {e}")
        return False

def erase_appointment(patient_id: str, patient_name: str, patient_dob: str, date: str, time: str) -> bool:
    try:                
        with open('knowledge/clinic_appointments.txt', 'r') as f:
            content = f.read()
        
        appointments = content.split('---APPOINTMENT RECORD START---')

        updated_content = textwrap.dedent("""========================================
        ACTIVE APPOINTMENTS
        ========================================""")
        for appointment in appointments:
            if 'APPOINTMENT RECORD END' not in appointment:
                continue
            elif f"DATE: {date}" in appointment and f"TIME: {time}" in appointment:
                if f"PATIENT_ID: {patient_id}" in appointment and f"PATIENT_NAME: {patient_name}" in appointment and f"PATIENT_DOB: {patient_dob}" in appointment:
                    continue
            else:
                updated_content += "---APPOINTMENT RECORD START---\n" + appointment + "\n"


        updated_content += textwrap.dedent("""========================================
        END OF APPOINTMENTS DATABASE
        =========================================""")

        with open('knowledge/clinic_appointments.txt', 'w') as f:
            f.write(updated_content)

        print(f"✅ Appointment erased from file")
        return True
        
    except Exception as e:
        print(f"🔴 Failed to erase appointment: {e}")
        return False
    
def handle_booking(self):

    if not self.state.payload.get('desired_date') or not self.state.payload.get('desired_time'):
        response = "🔴: Appointment informations missing. Please, specifiy the date and time of the desired booking"
        self.state.messages.append({"role": "assistant", "content": response})
        return None
        
    desired_date = self.state.payload.get('desired_date')
    desired_time = self.state.payload.get('desired_time')
    patient_name = self.state.user_identity.get("full name")
    patient_dob = self.state.user_identity.get("date")
    patient_id = get_patient_id(patient_name, patient_dob)
        
    if not patient_id:
        response = f"I couldn't find your patient record. Please contact our office directly."
        self.state.messages.append({"role": "assistant", "content": response})
        return None
        
    is_available = check_appointment(desired_date, desired_time)
        

    if not is_available:
        response = f"I'm sorry, but the slot on {desired_date} at {desired_time} is not available."
        self.state.messages.append({"role": "assistant", "content": response})
        return None
    else:
        success = write_appointment(patient_id, patient_name, patient_dob, desired_date, desired_time)
    
        if success:
            response = f"Great! I've successfully booked your appointment on {desired_date} at {desired_time}. You'll receive a confirmation email shortly."
            print(f"⚕️: {response}")
            self.state.messages.append({"role": "assistant", "content": response})
        else:
            response = "I encountered an error while booking your appointment. Please try again or contact our office directly."
            print(f"⚕️: {response}")
            self.state.messages.append({"role": "assistant", "content": response})
        
    return None

def handle_cancelling(self):
    if not self.state.payload.get('appointment_date') or not self.state.payload.get('appointment_time'):
        response = "🔴: Appointment informations missing. Please, specifiy the date and time of the desired booking"
        self.state.messages.append({"role": "assistant", "content": response})
        return None
    
    appointment_date = self.state.payload.get('appointment_date')
    appointment_time = self.state.payload.get('appointment_time')
    patient_name = self.state.user_identity.get("full name")
    patient_dob = self.state.user_identity.get("date")
    patient_id = get_patient_id(patient_name, patient_dob)

    if not patient_id:
        response = f"I couldn't find your patient record. Please contact our office directly."
        self.state.messages.append({"role": "assistant", "content": response})
        return None

    found = find_appointment(appointment_date, appointment_time, patient_name, patient_dob, patient_id)

    if not found:
        response = f"I couldn't find any appointment in your name in date {appointment_date} at hour {appointment_time}. Please contact our office directly."
        self.state.messages.append({"role": "assistant", "content": response})
        return None
    else:
        success = erase_appointment(patient_id, patient_name, patient_dob, appointment_date, appointment_time)

        if success:
            response = f"Great! I've successfully cancelled your appointment on {appointment_date} at {appointment_time}. You'll receive a confirmation email shortly."
            self.state.messages.append({"role": "assistant", "content": response})
        else:
            response = "I encountered an error while cancelling your appointment. Please try again or contact our office directly."
            self.state.messages.append({"role": "assistant", "content": response})
    
    return None

def handle_download_record(self) -> str:

    patient_name = self.state.user_identity.get('full name')
    patient_dob = self.state.user_identity.get('date')
    patient_id = get_patient_id(patient_name, patient_dob)

    try:
        with open('knowledge/clinic_DB.txt', 'r') as f:
            content = f.read()
        
        # Parse all active appointments
        records = content.split('---PATIENT RECORD START---')
        
        for record in records:
            if 'PATIENT RECORD END' not in record:
                continue
            
            if f"PATIENT_ID: {patient_id}" in record and f"FULL_NAME: {patient_name}" in record and f"DATE_OF_BIRTH: {patient_dob}" in record:
                response = "====DISPLAYING MEDICAL RECORD===="
                response = f"""
                ====DISPLAYING MEDICAL RECORD FOR PATIENT {patient_name}====

                {record.replace("---PATIENT RECORD END---", "")}
                
                ============================================================
                """
                return textwrap.dedent(response)
               
        return ""
    except Exception as e:
        print(f"🔴 Failed to check report: {e}")
        return ""

class ConversationalState(BaseModel):
    messages: list[dict] = []
    user_verified: bool = False
    user_identity: dict = {}
    user_auth_attempt: bool = False
    user_book_attempt: bool = False
    user_cancel_attempt: bool = False
    payload: dict = {}

class MedicFlow(Flow[ConversationalState]):

    def __init__(self, agents_config: dict, tasks_config: dict, state: ConversationalState):
        super().__init__()
        self.agents_config = agents_config
        self.tasks_config = tasks_config

        self.state.messages = state.messages
        self.state.user_verified = state.user_verified
        self.state.user_identity = state.user_identity
        self.state.user_auth_attempt = state.user_auth_attempt
        self.state.user_book_attempt = state.user_book_attempt
        self.state.user_cancel_attempt = state.user_cancel_attempt
        self.state.payload = state.payload

    @start()
    def beginning(self):
        return None

    @router(beginning)
    async def pre_process_user_intent(self):

        #print(f"""
        #      Currently, user_verified is {self.state.user_verified}
        #      user_auth_attempt is {self.state.user_auth_attempt}
        #      user_book_attempt is {self.state.user_book_attempt}
        #      user_cancel_attempt is {self.state.user_cancel_attempt}""")
        
        # If true, the user has provided a payload to authenticate, which must be verified
        if(self.state.user_auth_attempt):
            authentication_result = await check_identity(
                agent_config=self.agents_config['identity_verification_agent'],
                task_config=self.tasks_config['identity_verification'],
                payload=self.state.payload,
                file_path='knowledge/clinic_DB.txt'
            )
            self.state.messages.append({"role": "assistant", "content": authentication_result})
            return None
        
        #If true, the user has provided a payload to book an appointment
        if(self.state.user_book_attempt):
            if(self.state.user_verified):
                handle_booking(self)
            else:
                self.state.messages.append({"role": "assistant", "content": "Received booking, but the user isn't authenticated!"})
            return None
        
        #If true, the user has provided a payload to cancel a booked appointment
        if(self.state.user_cancel_attempt):
            if(self.state.user_verified):
                handle_cancelling(self)
            else:
                self.state.messages.append({"role": "assistant", "content": "Received cancel booking, but the user isn't authenticated!"})
            return None

        # If no flag has triggered so far, it's a defualt interaction, where we must classify between "requires authentication" and "doesn't require authentication"
        intent = await get_intent(
            conversation_context=self.state.messages,
            agent_config=self.agents_config['classifier'],
            task_config=self.tasks_config['intent_classification']
        )

        print(f"⚕️: Classified intent: {intent}")

        if "verification" in intent:
            # User requested operation that DOES require authentification

            if(not self.state.user_verified):
                # This triggers the main function that creates the payload
                self.state.messages.append({"role": "assistant", "content": "To execute this procedure, you must first authenticate. Redirecting to authentification procedure..."})
                return None
            elif(self.state.user_verified):

                operation = await get_operation(
                    conversation_context=self.state.messages,
                    agent_config=self.agents_config['classifier'],
                    task_config=self.tasks_config['operation_classification']
                )

                print(f"⚕️: Classified operation: {operation}")

                if "book" in operation:
                    self.state.messages.append({"role": "assistant", "content": "Redirecting to appointment booking procedure..."})
                    return None
                elif "cancel" in operation:
                    self.state.messages.append({"role": "assistant", "content": "Redirecting to appointment cancelling procedure..."})
                    return None
                elif "consult" in operation:
                    #record = handle_download_record(self)

                    record = await get_record(
                        conversation_context=self.state.messages,
                        agent_config=self.agents_config['private_data_retrieval_agent'],
                        task_config=self.tasks_config['private_data_retrieval_task'],
                        user_identity=self.state.user_identity,
                        file_path='knowledge/clinic_DB.txt'
                    )


                    if "violation" in record:
                        reply = record
                    else:
                        try:         
                            with open('knowledge/user_devices/email.txt', 'w') as f:
                                f.write(record)
                        except Exception as e:
                            print(f"🔴 Failed to write appointment: {e}")

                        reply = "result sent in your e-mail! (email.txt)"
                    self.state.messages.append({"role": "assistant", "content": reply})
                    return None
                else:
                    print("⚕️: Default option")
                    return None

        print(f"⚕️: Initiate general info")
        # User requested operation that doesn't need authentification
        reply = await get_generic_reply(
            conversation_context=self.state.messages,
            agent_config=self.agents_config['general_info_agent'],
            task_config=self.tasks_config['general_info_response'],
            file_path='knowledge/clinic_public_info.txt'
        )

        self.state.messages.append({"role": "assistant", "content": reply})
        return None
        

# Solutions missing: 2fa, Filter Agent