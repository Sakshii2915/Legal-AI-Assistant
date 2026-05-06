# Known corrections for the new Indian Laws (BNS, BNSS, BSA) 
# where LLMs often hallucinate based on old IPC/CrPC section numbers.

KNOWN_CORRECTIONS = {
    "175 bnss": (
        "Section 175 of the Bharatiya Nagarik Suraksha Sanhita (BNSS) relates to the 'Power of officer in charge of police station to investigate cognizable case' "
        "(formerly Section 156 of CrPC). \n"
        "- Section 175(3) BNSS: A Magistrate can order a police investigation or FIR.\n"
        "- Section 175(4) BNSS: Provides extra safeguards when a complaint is against a public servant, "
        "requiring the Magistrate to consider a report from the officer's superior and limiting the power to order an FIR without proper scrutiny."
    ),
    "175 of bnss": "Section 175 of the BNSS deals with the police's power to investigate cognizable cases and the Magistrate's oversight, especially regarding public servants.",
    "section 175 bnss": "Section 175 BNSS is about the investigation of cognizable cases and magisterial orders, replacing Section 156 of the CrPC.",
    "302 bns": "In the new law (BNS), Section 302 pertains to 'Snatching'. Punishment for Murder is now under Section 103 of the Bharatiya Nyaya Sanhita (BNS).",
    "103 bns": "Section 103 of the Bharatiya Nyaya Sanhita (BNS) provides the punishment for murder, replacing Section 302 of the IPC.",
    "106 bns": "Section 106 of the BNS deals with 'Causing death by negligence'. Section 106(2) specifically relates to hit-and-run cases with stricter punishments.",
    "bns 106": "Section 106 BNS relates to death by negligence (hit and run), formerly under IPC 304A.",
    "420 bns": "In the BNS, 'Cheating' is now covered under Section 318, not 420. Section 318 BNS replaces Section 420 of the IPC.",
    "318 bns": "Section 318 of the Bharatiya Nyaya Sanhita (BNS) pertains to Cheating, replacing Section 420 of the IPC.",
}

def get_correction(query):
    query_lower = query.lower()
    for key, correction in KNOWN_CORRECTIONS.items():
        if key in query_lower:
            return correction
    return None
