# IMPORTS
import urllib
import pandas as pd
import inquirer
import requests
from fuzzywuzzy import fuzz
import json

import nltk

nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Import data
stop_words = set(stopwords.words("english"))
symptoms_list = pd.read_csv('./SymptomsAndComplaints.csv')
blood_list = pd.read_csv('./BloodTypes.csv')
marital_list = pd.read_csv('./MaritalStatusTypes.csv')
employment_list = pd.read_csv('./EmploymentStatusTypes.csv')
gender_list = pd.read_csv('./GenderTypes.csv')
race_list = pd.read_csv('./RaceTypes.csv')
medications_list = pd.read_csv('./Medications.csv')


# CharmHealth endpoint calls
def getAccessToken():
    url = 'https://pen-accounts.charmtracker.com/oauth/v2/token?refresh_token=1000.4fd42a159399edb1c949afc551d1653a.037ed8ed6189d27f92a24ef8d987cfa7&client_id=1000.1BJ3ZXF421BH5MU1BRHEJTBJF7111H&client_secret=99cd58b7df4a92a3fb5be11761eee2eee7c5944c9d&redirect_uri=https%3A%2F%2Fsandboxehr.charmtracker.com%2Fehr%2Fphysician%2FmySpace.do%3FACTION%3DSHOW_OAUTH_JSON&grant_type=refresh_token'
    headers = {'content-type': 'application/json'}
    r = requests.post(url, headers=headers)
    return r.json()


access_token_data = getAccessToken()
# print(access_token_data)
access_token = access_token_data['access_token']
#access_token = '1000.e879c801d0b70545857dcf5be493966f.79acd496fa1d7e3cd6ca10122724eb86b'


def getMembers():
    url = 'https://sandboxehr.charmtracker.com/api/ehr/v1/members'
    authorization = "Bearer " + access_token
    headers = {
        'Authorization': authorization,
        'api_key': '182d0f0482bf9878c2a25dc242b3fd96',
    }
    r = requests.get(url, headers=headers)
    print(r)
    print(r.json())
    return r.json()


def getFacilities():
    url = 'https://sandboxehr.charmtracker.com/api/ehr/v1/facilities'
    authorization = "Bearer " + access_token
    headers = {
        'Authorization': authorization,
        'api_key': '182d0f0482bf9878c2a25dc242b3fd96',
    }
    r = requests.get(url, headers=headers)
    return r.json()
    # print(r.json())


patient_info = {
    "basic": [],
    "concerns": []
}


# FUNCTIONS
# test_NLTK - prints the tokens of a sample sentence for testing purposes.
def test_NLTK():
    print("I eat bread jam and cereal")
    words = word_tokenize("I eat bread jam and cereal for breakfast")
    filtered_sentence = [w for w in words if not w in stop_words]
    tagged_sentence = nltk.pos_tag(filtered_sentence)
    for pair in tagged_sentence:
        print("[ " + pair[0] + " ] is a [ " + pair[1] + " ]")


# run_bot - runs the overall bot to collect different information.
def run_bot():
    print("Welcome to CharmHealth.")
    status = [
        inquirer.List('status',
                      message="Are you a new patient?",
                      choices=['Yes', 'No'], ),
    ]

    info = inquirer.prompt(status)
    print(info)
    if info["status"] == 'Yes':
        run_new_patient_bot()
    else:
        run_returning_patient_bot()
    print("Thank you for your information! The doctor will be with you shortly.")


def run_returning_patient_bot():
    if greetings_bot(True) == False:
        symptoms_bot()
        medications_bot()


def run_new_patient_bot():
    if greetings_bot(False) == False:
        basic_info_bot([])
        basic_selection_questions([])
        symptoms_bot()
        medications_bot()


def get_nouns(sentence, description):
    words = word_tokenize(sentence)
    filtered_sentence = [w for w in words if not w in stop_words]
    tagged_sentence = nltk.pos_tag(filtered_sentence)
    nouns = []
    for pair in tagged_sentence:
        # print(pair)
        if pair[1] in description:
            nouns.append(pair[0])
    return nouns


# basic_info_bot - collects basic information
def basic_info_bot(already_entered):
    questions = basic_input_questions(already_entered)
    size = len(questions)
    counter = 0
    answers = []
    while counter < size:  # infinite loop
        user_input = input(questions[counter][0])
        nouns = get_nouns(user_input, questions[counter][1])
        answers.append(nouns)
        counter = counter + 1
    patient_info["basic"] = answers


def basic_input_questions(already_entered):
    questions = [
        ("What is your name? (First letter capitalized): ", ("NNP")),
        ("Are you male, female, or other? ", ("NN", "JJ")),
        ("How many years old are you? ", ("CD")),
        ("What is your race/ethicity? ", ("JJ", "NNP")),
        ("What is your phone number in the format XXX-XXX-XXXX? ", ("JJ")),
        ("What is your birthdate in the format MM/DD/YYYY? ", ("CD"))
    ]
    delete = 0
    for index in already_entered:
        del questions[index - delete]
        delete = delete + 1;
    return questions


def symptoms_bot():
    symptoms_and_complaints = []
    input_symptoms = []

    while True:
        user_symptom = input(
            "Please continue typing any concerns you want the doctor to know about! Type \"exit\" to submit! ")
        if user_symptom.lower() == "exit": break
        symptom_string = ""
        for str1 in symptoms_list['Symptoms']:
            for str2 in user_symptom.split(" "):
                Ratio = fuzz.ratio(str1.lower(), str2.lower())
                if Ratio > 90:
                    input_symptoms.append(str1)
                    symptom_string += (", " + str1)
        symptom_string = symptom_string[2:]
        print("We have detected: " + symptom_string)
    frequencies = []
    degrees = []
    onsets = []
    print("We will now ask you some questions about your concerns.")
    # time.sleep(2);
    for symptom in input_symptoms:
        input_freq = input("How frequent do you experience " + symptom + "? ")
        input_degree = input("How bad is your " + symptom + " from a scale from 1 - 5? ")
        input_onset = input("When did you start experiencing " + symptom + "? ")
        frequencies.append(input_freq)
        degrees.append(input_degree)
        onsets.append(input_onset)
    values = [input_symptoms, frequencies, degrees, onsets]
    patient_info["concerns"] = values


def medications_bot():
    medications = []
    input_medications = []

    while True:
        user_medication = input(
            "Please continue typing any medications you want the doctor to know about! Type \"exit\" to submit! ")
        if user_medication.lower() == "exit": break
        medication_string = ""
        for str1 in medications_list['Medications']:
            if str1.lower() in user_medication.lower():
                medication_string += (", " + str1)
        medication_string = medication_string[2:]
        medications.append(medication_string)
        print("We have detected: " + medication_string)
    amount = []
    start = []
    print("We will now ask you some questions about your medications.")
    # time.sleep(2);
    for medication in medications:
        input_amount = input("What dosage of " + medication + " do you use? ")
        input_start = input("When did you start using " + medication + "? ")
        amount.append(input_amount)
        start.append(input_start)
    values = [medications, amount, start]
    print(values)
    patient_info["medications"] = values


def basic_selection_questions(already_entered):
    topics = ['blood', 'marital', 'employment', 'alcohol', 'tobacco']
    questions = [
        inquirer.List('blood',
                      message="What is your blood type?",
                      choices=['A+', 'B+', 'AB+', 'O+', 'A-', 'B-', 'AB-', 'O-'], ),
        inquirer.List('marital',
                      message="What is your marital status?",
                      choices=['Married', 'Single', 'Divorced', 'Widowed', 'Widower'], ),
        inquirer.List('employment',
                      message="What is your employment status?",
                      choices=['Full-time', 'Part-time', 'Student', 'Unemployed', 'Searching'], ),
        inquirer.List('alcohol',
                      message="Do you use alcohol?",
                      choices=['Yes', 'No'], ),
        inquirer.List('tobacco',
                      message="Do you use tobacco?",
                      choices=['Yes', 'No'], ),
    ]
    delete = 0
    for index in already_entered:
        del questions[index - delete]
        del topics[index - delete]
        delete = delete + 1;
    info = inquirer.prompt(questions)
    answers = []
    for ele in topics:
        answers.append(info[ele])
    print(answers)
    return answers


def greetings_bot(status):
    info_dict = {
        "blood": "",
        "marital": "",
        "employment": "",
        "alcohol": "",
        "tobacco": "",
        "name": "",
        "gender": "",
        "age": "",
        "race": "",
        "phone": "",
        "birthdate": ""
    }
    response = input(
        "Please describe yourself and your reasoning for visiting! (or type \"questionnaire\" for the questionnaire)")
    if response == 'questionnaire':
        return False;

    found = []
    for str1 in response.split(" "):
        for str2 in blood_list['Blood']:
            Ratio = fuzz.ratio(str1.lower(), str2.lower())
            if Ratio > 90:
                info_dict["blood"] = str2
                found.append(0)
        for str2 in marital_list['Marital']:
            Ratio = fuzz.ratio(str1.lower(), str2.lower())
            if Ratio > 90:
                info_dict["marital"] = str2
                found.append(1)
        for str2 in employment_list['Employment']:
            Ratio = fuzz.ratio(str1.lower(), str2.lower())
            if Ratio > 90:
                info_dict["employment"] = str2
                found.append(2)

        for str2 in gender_list['Gender']:
            Ratio = fuzz.ratio(str1.lower(), str2.lower())
            if Ratio > 90:
                info_dict["gender"] = str2
        for str2 in race_list['Race']:
            Ratio = fuzz.ratio(str1.lower(), str2.lower())
            if Ratio > 90:
                info_dict["race"] = str2

    # Verify
    for entry in info_dict:
        if info_dict.get(entry) != "":
            verify = [
                inquirer.List('check',
                              message="You entered " + info_dict.get(entry) + " for " + entry + ". Is this correct? ",
                              choices=['Yes', 'No'], ),
            ]

            info = inquirer.prompt(verify)
            if info["check"] == 'No':
                new_answer = input("Please enter the correct information for " + entry + ": ")
                info_dict[entry] = new_answer

    # fill in empty
    basic_filled = []
    if info_dict["blood"] != "":
        basic_filled.append(0)
    if info_dict["marital"] != "":
        basic_filled.append(1)
    if info_dict["employment"] != "":
        basic_filled.append(2)

    info_filled = []
    if info_dict['gender'] != "":
        info_filled.append(1)
    if info_dict['race'] != "":
        info_filled.append(3)

    basic_selection_questions(basic_filled)
    basic_info_bot(info_filled)
    symptoms_bot()
    medications_bot()


def get_doctors():
    members = getMembers()
    print('MEMBERS')
    print(members)

    doctors = members["members"]
    print('DOCTORS')

    doctor_arr= []
    for dr in doctors:
        doctor_name = dr["prefix"] + ". " + dr["first_name"] + " " + dr["last_name"]
        print(doctor_name)
        doctor_arr.append(doctor_name)
    return doctor_arr



def schedule_appointment():
    doctors = get_doctors()


schedule_appointment()

# PROGRAM
# medications_bot()
# run_bot()
# testNLTK()
