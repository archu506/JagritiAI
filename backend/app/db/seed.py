"""
Seeds the database with synthetic demo data so the full SIH demo flow works
end-to-end with zero manual data entry and zero external API calls.
Run with: python -m app.db.seed
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, Base, engine
from app.models.user import User, UserRole, ConsentRecord  # noqa: F401 - registers tables on Base.metadata
from app.models.knowledge import KnowledgeDocument
from app.models.content import HealthScheme, MythFact, HealthFacility
from app.models.health import AnonymizedSymptomReport, HealthQuery, EarlyAwarenessSignal  # noqa: F401
from app.services.privacy import iso_week_bucket
from app.core.security import hash_password

# Demo accounts, provisioned directly here (not through the public
# /auth/register endpoint, which only ever creates citizen accounts - see
# app/api/v1/auth.py). This is the intended, secure way to bootstrap
# privileged accounts for the SIH demo.
DEMO_ACCOUNTS = [
    {"full_name": "Demo Citizen", "email": "citizen@demo.jagriti", "password": "Demo@1234",
     "role": UserRole.citizen, "district": "Khordha", "state": "Odisha"},
    {"full_name": "Dr. Demo Official", "email": "official@demo.jagriti", "password": "Demo@1234",
     "role": UserRole.health_official, "district": "Khordha", "state": "Odisha"},
    {"full_name": "Demo ASHA Worker", "email": "asha@demo.jagriti", "password": "Demo@1234",
     "role": UserRole.asha_worker, "district": "Khordha", "state": "Odisha"},
    {"full_name": "Demo Admin", "email": "admin@demo.jagriti", "password": "Demo@1234",
     "role": UserRole.admin, "district": None, "state": None},
]

KNOWLEDGE_DOCS = [
    # English documents
    {
        "title": "Dengue Fever: Symptoms and Prevention", "topic_tag": "dengue", "category": "vector_borne",
        "authority_score": 90, "published_date": "2025-06-01", "language": "en",
        "source_name": "NCDC (National Centre for Disease Control)",
        "source_url": "https://ncdc.gov.in",
        "content": ("Dengue fever causes high fever, severe headache, pain behind the eyes, "
                    "joint and muscle pain, and skin rash. It spreads through the bite of an "
                    "infected Aedes mosquito, which breeds in clean stagnant water. Prevention "
                    "includes removing stagnant water around homes, using mosquito nets and "
                    "repellents, and wearing full-sleeved clothing. Seek medical care immediately "
                    "if fever persists beyond two days, or if there is bleeding, severe abdominal "
                    "pain, or persistent vomiting, as these can indicate severe dengue."),
    },
    {
        "title": "Malaria: Symptoms and Prevention", "topic_tag": "malaria", "category": "vector_borne",
        "authority_score": 90, "published_date": "2025-05-15", "language": "en",
        "source_name": "NCDC (National Centre for Disease Control)",
        "source_url": "https://ncdc.gov.in",
        "content": ("Malaria causes fever with chills and sweating, headache, nausea, and body "
                    "aches, typically appearing 10-15 days after being bitten by an infected "
                    "Anopheles mosquito. Unlike dengue, malaria fever often comes in cycles. "
                    "Prevention includes sleeping under insecticide-treated mosquito nets, "
                    "eliminating standing water, and using repellents at dusk and dawn when "
                    "Anopheles mosquitoes are most active. Diagnosis requires a blood test; seek "
                    "medical care promptly for any cyclical fever, especially in malaria-endemic areas."),
    },
    {
        "title": "Diabetes: Early Signs and Management", "topic_tag": "diabetes", "category": "chronic_disease",
        "authority_score": 85, "published_date": "2025-03-10", "language": "en",
        "source_name": "MoHFW (Ministry of Health and Family Welfare)",
        "source_url": "https://mohfw.gov.in",
        "content": ("Type 2 diabetes often develops gradually, with early signs including "
                    "increased thirst, frequent urination, fatigue, blurred vision, and slow-healing "
                    "wounds. Risk factors include family history, obesity, and sedentary lifestyle. "
                    "Management involves regular blood sugar monitoring, a balanced diet low in "
                    "refined sugar, regular physical activity, and medication as prescribed by a "
                    "doctor. Regular check-ups help prevent complications affecting the eyes, "
                    "kidneys, and nerves."),
    },
    {
        "title": "Diarrheal Disease and Oral Rehydration", "topic_tag": "diarrhea", "category": "gastrointestinal",
        "authority_score": 95, "published_date": "2025-04-20", "language": "en",
        "source_name": "WHO", "source_url": "https://who.int",
        "content": ("Diarrhea is often caused by contaminated food or water, and can lead to "
                    "dangerous dehydration, especially in children. The first response is oral "
                    "rehydration solution (ORS) mixed with clean water, plus zinc supplementation "
                    "for children. Continue feeding during recovery. Seek medical attention if there "
                    "is blood in stool, high fever, signs of severe dehydration (sunken eyes, very "
                    "little urine, extreme thirst), or if diarrhea lasts more than two days."),
    },
    {
        "title": "Understanding Seasonal Influenza", "topic_tag": "flu", "category": "respiratory",
        "authority_score": 90, "published_date": "2025-05-01", "language": "en",
        "source_name": "NCDC", "source_url": "https://ncdc.gov.in",
        "content": ("Seasonal influenza (flu) causes fever, cough, sore throat, body aches, and "
                    "fatigue, typically resolving within a week with rest and fluids. It spreads "
                    "through respiratory droplets. Most people recover at home with paracetamol for "
                    "fever, plenty of fluids, and rest. Seek care urgently if there is difficulty "
                    "breathing, persistent chest pain, or symptoms that worsen after initially "
                    "improving, especially in young children, elderly people, or those with chronic "
                    "conditions."),
    },
    {
        "title": "Skin Rashes: Common Causes", "topic_tag": "rash", "category": "skin_allergy",
        "authority_score": 80, "published_date": "2025-02-15", "language": "en",
        "source_name": "NCDC", "source_url": "https://ncdc.gov.in",
        "content": ("Skin rashes can result from allergic reactions, infections such as chickenpox "
                    "or measles, heat, or insect bites. A rash accompanied by high fever, joint pain "
                    "or spreading rapidly may indicate a viral infection like dengue or measles and "
                    "should be evaluated by a doctor. Keep the affected area clean and avoid "
                    "scratching. Antihistamines can relieve itching for allergic rashes, but a "
                    "medical professional should assess any rash with fever."),
    },
    {
        "title": "Fever: General Guidance (When to See a Doctor)",
        "topic_tag": "fever_general", "category": "fever_cluster",
        "authority_score": 85, "published_date": "2025-07-01", "language": "en",
        "source_name": "MoHFW (Ministry of Health and Family Welfare)",
        "source_url": "https://mohfw.gov.in",
        "content": ("Fever is a common symptom of many different illnesses, from viral infections "
                    "to more serious conditions, and by itself does not indicate a specific disease. "
                    "General care includes rest, fluids, and paracetamol as needed for comfort. See "
                    "a doctor if fever exceeds 103°F (39.4°C), lasts more than two days, is "
                    "accompanied by rash, severe headache, difficulty breathing, or persistent "
                    "vomiting, or occurs in an infant under 3 months. A doctor can determine the "
                    "underlying cause through examination and, if needed, testing for specific "
                    "conditions such as dengue, malaria, or typhoid based on your symptoms and region."),
    },

    # Hindi documents
    {
        "title": "डेंगू बुखार: लक्षण और रोकथाम (Dengue Symptoms & Prevention)",
        "topic_tag": "dengue", "category": "vector_borne",
        "authority_score": 90, "published_date": "2025-06-01", "language": "hi",
        "source_name": "NCDC (राष्ट्रीय रोग नियंत्रण केंद्र)",
        "source_url": "https://ncdc.gov.in",
        "content": ("डेंगू बुखार के मुख्य लक्षणों में तेज़ बुखार, सिरदर्द, आंखों के पीछे दर्द, "
                    "जोड़ों और मांसपेशियों में दर्द तथा त्वचा पर चकत्ते शामिल हैं। यह संक्रमित एडिस "
                    "मच्छर के काटने से फैलता है जो साफ ठहरे हुए पानी में पनपता है। बचाव के लिए "
                    "अपने आसपास पानी न जमा होने दें, मच्छरदानी व मॉस्किटो रिपेलेंट का उपयोग करें और "
                    "पूरी आस्तीन के कपड़े पहनें। यदि बुखार 2 दिन से अधिक रहता है या रक्तस्राव अथवा "
                    "गंभीर पेट दर्द होता है तो तुरंत डॉक्टर से संपर्क करें।"),
    },
    {
        "title": "मलेरिया: लक्षण और रोकथाम (Malaria Symptoms & Prevention)",
        "topic_tag": "malaria", "category": "vector_borne",
        "authority_score": 90, "published_date": "2025-05-15", "language": "hi",
        "source_name": "NCDC (राष्ट्रीय रोग नियंत्रण केंद्र)",
        "source_url": "https://ncdc.gov.in",
        "content": ("मलेरिया में ठंड और पसीने के साथ रुक-रुक कर तेज़ बुखार आता है, साथ ही सिरदर्द, "
                    "जी मिचलाना और शरीर में दर्द होता है। यह एनोफिलीज मच्छर के काटने से फैलता है। "
                    "बचाव के लिए कीटनाशक-उपचारित मच्छरदानी का प्रयोग करें, आसपास पानी न जमा होने दें "
                    "और सुबह-शाम मच्छर भगाने वाले साधनों का उपयोग करें। बुखार होने पर तुरंत खून की जांच "
                    "कराएं और डॉक्टर से सलाह लें।"),
    },
    {
        "title": "दस्त रोग और ओआरएस (ORS) प्रबंधन",
        "topic_tag": "diarrhea", "category": "gastrointestinal",
        "authority_score": 95, "published_date": "2025-04-20", "language": "hi",
        "source_name": "WHO (विश्व स्वास्थ्य संगठन)",
        "source_url": "https://who.int",
        "content": ("दस्त दूषित भोजन या पानी से होता है और इससे शरीर में खतरनाक डिहाइड्रेशन "
                    "(पानी की कमी) हो सकती है। सबसे पहला उपचार साफ पानी में मिलाया गया ओआरएस (ORS) "
                    "घोल और जिंक की गोलियां हैं। दस्त के दौरान भोजन देना जारी रखें। यदि मल में खून "
                    "आए, तेज़ बुखार हो या बच्चा बहुत सुस्त दिखे तो तुरंत डॉक्टर से संपर्क करें।"),
    },
    {
        "title": "बुखार: सामान्य मार्गदर्शन और देखभाल",
        "topic_tag": "fever_general", "category": "fever_cluster",
        "authority_score": 85, "published_date": "2025-07-01", "language": "hi",
        "source_name": "MoHFW (स्वास्थ्य एवं परिवार कल्याण मंत्रालय)",
        "source_url": "https://mohfw.gov.in",
        "content": ("बुखार शरीर में संक्रमण का एक सामान्य लक्षण है और स्वयं में कोई बीमारी नहीं है। "
                    "सामान्य देखभाल में पर्याप्त आराम, प्रचुर मात्रा में तरल पदार्थ और आवश्यकतानुसार "
                    "पैरासिटामोल शामिल है। यदि बुखार 103°F से अधिक हो, 2 दिन से ज्यादा रहे, या साथ में "
                    "चकत्ते, सांस लेने में तकलीफ अथवा गंभीर सिरदर्द हो तो तुरंत डॉक्टर को दिखाएं।"),
    },

    # Odia documents
    {
        "title": "ଡେଙ୍ଗୁ ଜ୍ୱର: ଲକ୍ଷଣ ଏବଂ ପ୍ରତିଷେଧକ (Dengue Symptoms & Prevention)",
        "topic_tag": "dengue", "category": "vector_borne",
        "authority_score": 90, "published_date": "2025-06-01", "language": "or",
        "source_name": "NCDC (ଜାତୀୟ ରୋଗ ନିୟନ୍ତ୍ରଣ କେନ୍ଦ୍ର)",
        "source_url": "https://ncdc.gov.in",
        "content": ("ଡେଙ୍ଗୁ ଜ୍ୱରର ମୁଖ୍ୟ ଲକ୍ଷଣଗୁଡ଼ିକ ହେଲା ପ୍ରବଳ ଜ୍ୱର, ମୁଣ୍ଡବିନ୍ଧା, ଆଖି ପଛରେ ଯନ୍ତ୍ରଣା, "
                    "ଗଣ୍ଠି ଓ ମାଂସପେଶୀ ଯନ୍ତ୍ରଣା ଏବଂ ଚର୍ମରେ ରାସ୍। ଏହା ସଂକ୍ରମିତ ଏଡିସ୍ ମଶା କାମୁଡ଼ିବା ଦ୍ୱାରା "
                    "ବ୍ୟାପିଥାଏ। ପ୍ରତିଷେଧକ ପାଇଁ ଜମା ହୋଇଥିବା ସଫା ପାଣି ହଟାନ୍ତୁ, ମଶାରୀ ବ୍ୟବହାର କରନ୍ତୁ "
                    "ଏବଂ ସମ୍ପୂର୍ଣ୍ଣ ଢାଙ୍କି ହେଉଥିବା ପୋଷାକ ପିନ୍ଧନ୍ତୁ। ଜ୍ୱର ୨ ଦିନରୁ ଅଧିକ ରହିଲେ ତୁରନ୍ତ "
                    "ଡାକ୍ତରଙ୍କ ପରାମର୍ଶ ନିଅନ୍ତୁ।"),
    },
    {
        "title": "ମ୍ୟାଲେରିଆ: ଲକ୍ଷଣ ଏବଂ ପ୍ରତିଷେଧକ (Malaria Symptoms & Prevention)",
        "topic_tag": "malaria", "category": "vector_borne",
        "authority_score": 90, "published_date": "2025-05-15", "language": "or",
        "source_name": "NCDC (ଜାତୀୟ ରୋଗ ନିୟନ୍ତ୍ରଣ କେନ୍ଦ୍ର)",
        "source_url": "https://ncdc.gov.in",
        "content": ("ମ୍ୟାଲେରିଆରେ କମ୍ପ ସହ ଜ୍ୱର, ମୁଣ୍ଡବିନ୍ଧା ଏବଂ ଝାଳ ବୋହିବା ଭଳି ଲକ୍ଷଣ ଦେଖାଯାଏ। "
                    "ଏହା ଆନୋଫିଲିସ୍ ମଶା ଦ୍ୱାରା ବ୍ୟାପିଥାଏ। ପ୍ରତିଷେଧକ ପାଇଁ ମଶାରୀ ବ୍ୟବହାର କରନ୍ତୁ "
                    "ଏବଂ ଜମା ପାଣି ଦୂର କରନ୍ତୁ। ଜ୍ୱର ହେଲେ ତୁରନ୍ତ ରକ୍ତ ପରୀକ୍ଷା କରାନ୍ତୁ।"),
    },
    {
        "title": "ଝାଡ଼ା ରୋଗ ଏବଂ ଓଆରଏସ୍ (ORS) ସଚେତନତା",
        "topic_tag": "diarrhea", "category": "gastrointestinal",
        "authority_score": 95, "published_date": "2025-04-20", "language": "or",
        "source_name": "WHO (ବିଶ୍ୱ ସ୍ୱାସ୍ଥ୍ୟ ସଂଗଠନ)",
        "source_url": "https://who.int",
        "content": ("ଝାଡ଼ା ଦ୍ୱାରା ଶରୀରରେ ଜଳକଷ୍ଟ (Dehydration) ହୋଇଥାଏ। ପ୍ରଥମ ପ୍ରତିକାର ହେଉଛି "
                    "ସଫା ପାଣିରେ ଓଆରଏସ୍ (ORS) ଦ୍ରବଣ ମିଶାଇ ପିଇବାକୁ ଦେବା। ଝାଡ଼ା ସମୟରେ ଖାଦ୍ୟ "
                    "ଦେବା ଜାରି ରଖନ୍ତୁ ଏବଂ ଆବଶ୍ୟକ ହେଲେ ଡାକ୍ତରଙ୍କ ପରାମର୍ଶ ନିଅନ୍ତୁ।"),
    },
    {
        "title": "ଜ୍ୱର ସଚେତନତା ଏବଂ ସାଧାରଣ ମାର୍ଗଦର୍ଶନ",
        "topic_tag": "fever_general", "category": "fever_cluster",
        "authority_score": 85, "published_date": "2025-07-01", "language": "or",
        "source_name": "MoHFW (ସ୍ୱାସ୍ଥ୍ୟ ଏବଂ ପରିବାର କଲ୍ୟାଣ ମନ୍ତ୍ରଣାଳୟ)",
        "source_url": "https://mohfw.gov.in",
        "content": ("ଜ୍ୱର ଅନେକ ରୋଗର ସାଧାରଣ ଲକ୍ଷଣ। ବିଶ୍ରାମ ନିଅନ୍ତୁ, ପ୍ରଚୁର ପାଣି ଓ ତରଳ "
                    "ଖାଦ୍ୟ ପିଅନ୍ତୁ। ଜ୍ୱର ୨ ଦିନରୁ ଅଧିକ ରହିଲେ କିମ୍ବା ଅଧିକ ହେଲେ ତୁରନ୍ତ ଡାକ୍ତରଙ୍କ "
                    "ପରାମର୍ଶ ନିଅନ୍ତୁ।"),
    },
]

SCHEMES = [
    {
        "name": "Ayushman Bharat - PM Jan Arogya Yojana (PM-JAY)",
        "description": "Provides health cover of ₹5 lakh per family per year for secondary and tertiary care hospitalization.",
        "eligibility": "Families identified based on deprivation criteria in the SECC database.",
        "how_to_apply": "Visit the nearest Common Service Centre or empanelled hospital with your Ayushman card / eligibility ID.",
        "official_url": "https://pmjay.gov.in",
    },
    {
        "name": "Janani Suraksha Yojana (JSY)",
        "description": "Cash assistance for institutional delivery to reduce maternal and neonatal mortality.",
        "eligibility": "Pregnant women, with focus on those from BPL households and low-performing states.",
        "how_to_apply": "Register at the nearest Anganwadi centre or government health facility during pregnancy.",
        "official_url": "https://nhm.gov.in",
    },
    {
        "name": "National Programme for Prevention & Control of Non-Communicable Diseases",
        "description": "Free screening and management support for diabetes, hypertension, and common cancers at government facilities.",
        "eligibility": "All adults, with priority for those above 30 years of age.",
        "how_to_apply": "Visit your nearest Primary Health Centre or Health & Wellness Centre for a free screening.",
        "official_url": "https://main.mohfw.gov.in",
    },
]

MYTHS = [
    {"myth": "Dengue can spread from one person to another directly.", "fact": "Dengue only spreads through Aedes mosquito bites, not person-to-person contact.", "topic_tag": "dengue"},
    {"myth": "Drinking alcohol prevents dengue.", "fact": "Alcohol does not prevent dengue. Use verified prevention guidance such as mosquito protection and removal of stagnant water where mosquitoes breed.", "topic_tag": "dengue"},
    {"myth": "Diabetes is only caused by eating too much sugar.", "fact": "Type 2 diabetes results from a combination of genetics, weight, activity level, and diet — not sugar intake alone.", "topic_tag": "diabetes"},
    {"myth": "You should stop eating solid food entirely during diarrhea.", "fact": "Continued feeding with easily digestible food, alongside ORS, supports faster recovery, especially in children.", "topic_tag": "diarrhea"},
    {"myth": "Antibiotics cure the flu faster.", "fact": "Flu is caused by a virus; antibiotics only work on bacterial infections and don't help with the flu.", "topic_tag": "flu"},
    {"myth": "Only stagnant dirty water breeds dengue mosquitoes.", "fact": "Aedes mosquitoes that spread dengue breed in small amounts of CLEAN stagnant water, such as in flower pots, coolers, and discarded containers.", "topic_tag": "dengue"},
]

FACILITIES = [
    {"name": "Khordha District Headquarters Hospital", "facility_type": "District Hospital", "district": "Khordha", "state": "Odisha", "latitude": 20.1830, "longitude": 85.6189, "phone": "0674-2300123"},
    {"name": "Bhubaneswar PHC (New Capital)", "facility_type": "PHC", "district": "Khordha", "state": "Odisha", "latitude": 20.2961, "longitude": 85.8245, "phone": "0674-2400456"},
    {"name": "Cuttack SCB Medical College Hospital", "facility_type": "Medical College Hospital", "district": "Cuttack", "state": "Odisha", "latitude": 20.4625, "longitude": 85.8830, "phone": "0671-2414080"},
    {"name": "Puri CHC Sadar", "facility_type": "CHC", "district": "Puri", "state": "Odisha", "latitude": 19.8135, "longitude": 85.8312, "phone": "06752-223333"},
]

DISTRICTS = ["Khordha", "Cuttack", "Puri", "Ganjam"]
SYMPTOM_TAGS = ["fever", "cough", "diarrhea", "rash", "headache"]


def seed(db: Session = None):
    should_close = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True
    try:
        for acct in DEMO_ACCOUNTS:
            if not db.query(User).filter(User.email == acct["email"]).first():
                db.add(User(
                    full_name=acct["full_name"],
                    email=acct["email"],
                    hashed_password=hash_password(acct["password"]),
                    role=acct["role"],
                    district=acct["district"],
                    state=acct["state"],
                ))
        db.commit()
        print(f"Seeded {len(DEMO_ACCOUNTS)} demo accounts (citizen / health_official / admin)")

        existing_doc_count = db.query(KnowledgeDocument).count()
        if existing_doc_count < len(KNOWLEDGE_DOCS):
            existing_titles = {d.title for d in db.query(KnowledgeDocument).all()}
            for doc in KNOWLEDGE_DOCS:
                if doc["title"] not in existing_titles:
                    db.add(KnowledgeDocument(**doc))
            db.commit()
            print(f"Seeded knowledge documents (total {db.query(KnowledgeDocument).count()})")

        if db.query(HealthScheme).count() == 0:
            for s in SCHEMES:
                db.add(HealthScheme(**s, language="en"))
            print(f"Seeded {len(SCHEMES)} health schemes")

        if db.query(MythFact).count() == 0:
            for m in MYTHS:
                db.add(MythFact(**m, source_name="NCDC/WHO", language="en"))
            print(f"Seeded {len(MYTHS)} myth-fact pairs")

        if db.query(HealthFacility).count() == 0:
            for f in FACILITIES:
                db.add(HealthFacility(**f))
            print(f"Seeded {len(FACILITIES)} health facilities")

        if db.query(AnonymizedSymptomReport).count() == 0:
            # Synthetic historical trend data: 8 weeks of baseline noise, plus
            # a deliberate spike in the most recent week for one (symptom,
            # district) pair so the Early Awareness Engine has something
            # genuine to detect during the demo.
            random.seed(42)
            now = datetime.utcnow()
            count = 0
            for week_offset in range(8, 0, -1):
                week_dt = now - timedelta(weeks=week_offset)
                week_bucket = iso_week_bucket(week_dt)
                for district in DISTRICTS:
                    for tag in SYMPTOM_TAGS:
                        baseline = random.randint(3, 8)
                        for _ in range(baseline):
                            db.add(AnonymizedSymptomReport(
                                symptom_tag=tag, district_bucket=district,
                                week_bucket=week_bucket, created_at=week_dt,
                            ))
                            count += 1

            # Deliberate spike: dengue-adjacent symptom cluster (fever+rash) in
            # Khordha this current week, well above baseline -> should trigger
            # a 'high' severity Early Awareness Signal when the engine runs.
            current_week = iso_week_bucket(now)
            for tag in ["fever", "rash"]:
                for _ in range(22):
                    db.add(AnonymizedSymptomReport(
                        symptom_tag=tag, district_bucket="Khordha",
                        week_bucket=current_week, created_at=now,
                    ))
                    count += 1

            print(f"Seeded {count} synthetic anonymized symptom reports (with a deliberate Khordha fever/rash spike)")

        _seed_signal_plane_demo_data(db)

        db.commit()
        print("Seeding complete.")
    finally:
        if should_close:
            db.close()


def _seed_signal_plane_demo_data(db):
    """
    Seeds GeoBlock + SignalEvent (signal plane) with 28 days of realistic
    baseline noise across several blocks/topics, plus ONE deliberate,
    clearly-labeled simulated spike (vector_borne/malaria in Niali Block)
    so the AwarenessEngineV2 has something genuine to detect on demand,
    per proposal §18. All seeded events are marked is_simulated=True so the
    dashboard can clearly show "DEMO / SIMULATED DATA" and never confuse
    this with real public-health statistics.
    """
    from app.models.signals import GeoBlock, SignalEvent, Alert
    from app.services.awareness_v2 import AwarenessEngineV2

    blocks_data = [
        {"block_name": "Bhubaneswar Block", "district": "Khordha", "state": "Odisha", "latitude": 20.2961, "longitude": 85.8245},
        {"block_name": "Niali Block", "district": "Cuttack", "state": "Odisha", "latitude": 20.3667, "longitude": 85.9333},
        {"block_name": "Puri Sadar Block", "district": "Puri", "state": "Odisha", "latitude": 19.8135, "longitude": 85.8312},
    ]
    blocks = []
    for bd in blocks_data:
        existing = db.query(GeoBlock).filter(GeoBlock.block_name == bd["block_name"]).first()
        if not existing:
            existing = GeoBlock(**bd)
            db.add(existing)
            db.commit()
            db.refresh(existing)
        blocks.append(existing)

    niali = next(b for b in blocks if b.block_name == "Niali Block")
    now = datetime.utcnow()
    today_bucket = now.strftime("%Y-%m-%d")

    # Check if existing malaria historical baseline events have the intended ~12.0 baseline.
    niali_malaria_baseline_events = db.query(SignalEvent).filter(
        SignalEvent.geo_block_id == niali.id,
        SignalEvent.topic_category == "vector_borne",
        SignalEvent.topic_tag == "malaria",
        SignalEvent.day_bucket != today_bucket,
    ).all()

    avg_niali_malaria_baseline = (
        sum(e.count for e in niali_malaria_baseline_events) / len(niali_malaria_baseline_events)
        if niali_malaria_baseline_events else 0
    )

    should_reseed_events = (
        len(niali_malaria_baseline_events) == 0 or
        abs(avg_niali_malaria_baseline - 12.0) > 0.5 or
        db.query(SignalEvent).filter(SignalEvent.count == 180).first() is not None
    )

    if should_reseed_events:
        # DO NOT delete Alert rows! Only clear simulated SignalEvents so existing Alert assignment and field verifications are never destroyed.
        db.query(SignalEvent).filter(SignalEvent.is_simulated == 1).delete()
        db.commit()

        categories = ["vector_borne", "respiratory", "gastrointestinal", "fever_cluster"]
        count = 0
        baseline_pattern = [3, 21, 5, 19, 7, 17, 8, 16, 9, 15, 10, 14, 11, 13]
        # Topic-specific baseline pattern for Malaria in Niali Block:
        # 14-element pattern yielding mean = 12.0 and stddev = 6.13 across 28 days
        malaria_baseline_pattern = [12, 4, 20, 7, 17, 6, 18, 12, 4, 20, 7, 17, 5, 19]
        idx = 0

        for day_offset in range(28, 0, -1):
            day_dt = now - timedelta(days=day_offset)
            day_bucket = day_dt.strftime("%Y-%m-%d")
            for block in blocks:
                for category in categories:
                    if block.block_name == "Niali Block" and category == "vector_borne":
                        baseline = malaria_baseline_pattern[day_offset % len(malaria_baseline_pattern)]
                    else:
                        baseline = baseline_pattern[idx % len(baseline_pattern)]
                        idx += 1

                    db.add(SignalEvent(
                        topic_category=category,
                        topic_tag="malaria" if category == "vector_borne" else None,
                        geo_block_id=block.id,
                        day_bucket=day_bucket, count=baseline, is_simulated=1, created_at=day_dt,
                    ))
                    count += 1

        # Deliberate spike: malaria-like (vector_borne) query surge in Niali Block "today"
        # count=55 against baseline=12.0 gives observed=55, baseline=12.0, z ~ 7.00, multiplier ~ 4.6x
        db.add(SignalEvent(
            topic_category="vector_borne", topic_tag="malaria", geo_block_id=niali.id,
            day_bucket=today_bucket, count=55, is_simulated=1, created_at=now,
        ))
        count += 1

        db.commit()
        print(f"Seeded {count} signal-plane events across {len(blocks)} geo blocks "
              f"(DEMO/SIMULATED, includes deliberate Niali Block malaria spike with baseline ~12.0)")

    # Always re-evaluate AwarenessEngineV2 to update existing Alert database records in-place
    engine_v2 = AwarenessEngineV2(db)
    engine_v2.run_for_day(today_bucket)


if __name__ == "__main__":
    seed()
