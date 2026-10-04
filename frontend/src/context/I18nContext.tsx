import { createContext, useContext, useState, ReactNode } from "react";

export type Lang = "en" | "hi" | "or";

const STRINGS: Record<Lang, Record<string, string>> = {
  en: {
    appName: "JagritiAI",
    tagline: "AI-powered health awareness and early signal platform",
    askQuestion: "Ask a health question",
    askPlaceholder: "e.g. I have fever and joint pain, what could it be?",
    send: "Ask",
    login: "Login",
    register: "Register",
    logout: "Logout",
    dashboard: "Dashboard",
    schemes: "Health Schemes",
    myths: "Myth vs Fact",
    nearby: "Nearby Healthcare",
    govDashboard: "Government Dashboard",
    ashaPortal: "ASHA Worker Portal",
    assignAsha: "Assign ASHA Worker",
    verificationStatus: "Field Verification Status",
    fieldObservation: "Field Observation Notes",
    consentPrompt: "Would you like to anonymously contribute this to public health trend monitoring?",
    consentYes: "Yes, contribute anonymously",
    consentNo: "No thanks",
    disclaimerBanner: "JagritiAI provides general health information, not medical diagnosis. In an emergency, call 108.",
    landingSubtitle: "Community Health Sentinel",
    landingProblemTitle: "The problem",
    landingProblemText: "Early signs of local disease outbreaks — a cluster of fever cases, a rise in diarrhea questions in one block — often go unnoticed until they've already become a public health burden, because there's no simple way for everyday health questions to feed into district-level awareness.",
    landingSolutionTitle: "The solution",
    landingSolutionText: "JagritiAI lets citizens ask everyday health questions in their own language and get grounded, source-backed answers. With explicit consent, anonymized topic signals feed a statistical Early Awareness Engine that surfaces unusual patterns for health officials to review — never a diagnosis, always a human-verified signal.",
    askJagriti: "Ask JagritiAI",
    exploreDisease: "Explore Disease Awareness",
    forHealthOfficials: "For Health Officials",
    privacyTitle: "Your privacy, protected",
    privacyText: "Questions you ask are private by default. Only if you explicitly opt in does an anonymized topic tag — never your name, question text, or exact location — contribute to public health monitoring. You can decline every time.",
    aiDisclaimerTitle: "AI does not diagnose diseases",
    aiDisclaimerText: "JagritiAI shares general, source-backed health information and points you to trusted schemes and facilities. It never diagnoses a condition and never replaces a qualified doctor. In an emergency, always call 108.",
    flowTitle: "How a question becomes public health awareness",
    flowStep1Title: "1. Citizen asks",
    flowStep1Text: "You ask a health question and get a grounded answer, privately.",
    flowStep2Title: "2. Anonymous signal",
    flowStep2Text: "If you consent, only a de-identified topic and coarse location are added to an aggregate count — never your identity.",
    flowStep3Title: "3. Government awareness",
    flowStep3Text: "Health officials see only aggregate, anonymized trends and statistical alerts for human review — never individual data.",
  },
  hi: {
    appName: "जागृति AI",
    tagline: "AI-संचालित स्वास्थ्य जागरूकता और शीघ्र संकेत मंच",
    askQuestion: "स्वास्थ्य प्रश्न पूछें",
    askPlaceholder: "जैसे मुझे बुखार और जोड़ों में दर्द है, यह क्या हो सकता है?",
    send: "पूछें",
    login: "लॉगिन",
    register: "पंजीकरण करें",
    logout: "लॉगआउट",
    dashboard: "डैशबोर्ड",
    schemes: "स्वास्थ्य योजनाएं",
    myths: "भ्रम बनाम तथ्य",
    nearby: "नज़दीकी स्वास्थ्य सेवा",
    govDashboard: "सरकारी डैशबोर्ड",
    consentPrompt: "क्या आप इसे गुमनाम रूप से सार्वजनिक स्वास्थ्य ट्रेंड निगरानी में योगदान देना चाहेंगे?",
    consentYes: "हां, गुमनाम रूप से योगदान करें",
    consentNo: "नहीं धन्यवाद",
    disclaimerBanner: "जागृति AI सामान्य स्वास्थ्य जानकारी प्रदान करता है, चिकित्सा निदान नहीं। आपातकाल में 108 पर कॉल करें।",
    landingSubtitle: "सामुदायिक स्वास्थ्य संरक्षक",
    landingProblemTitle: "समस्या",
    landingProblemText: "स्थानीय बीमारी के प्रकोप के शुरुआती संकेत — जैसे किसी क्षेत्र में बुखार के मामलों का जमावड़ा — अक्सर तब तक ध्यान में नहीं आते जब तक वे सार्वजनिक स्वास्थ्य समस्या नहीं बन जाते, क्योंकि रोज़मर्रा के स्वास्थ्य प्रश्नों को जिला-स्तरीय जागरूकता से जोड़ने का कोई सरल तरीका नहीं है।",
    landingSolutionTitle: "समाधान",
    landingSolutionText: "जागृति AI नागरिकों को अपनी भाषा में स्वास्थ्य प्रश्न पूछने और स्रोत-आधारित उत्तर पाने देता है। स्पष्ट सहमति के साथ, गुमनाम विषय संकेत एक सांख्यिकीय अर्ली अवेयरनेस इंजन को फीड करते हैं जो असामान्य पैटर्न को स्वास्थ्य अधिकारियों की समीक्षा के लिए सामने लाता है — कभी निदान नहीं, हमेशा मानव-सत्यापित संकेत।",
    askJagriti: "जागृति AI से पूछें",
    exploreDisease: "रोग जागरूकता देखें",
    forHealthOfficials: "स्वास्थ्य अधिकारियों के लिए",
    privacyTitle: "आपकी गोपनीयता सुरक्षित है",
    privacyText: "आपके प्रश्न डिफ़ॉल्ट रूप से निजी हैं। केवल यदि आप स्पष्ट रूप से सहमति देते हैं, तभी एक गुमनाम विषय टैग — कभी आपका नाम, प्रश्न पाठ या सटीक स्थान नहीं — सार्वजनिक स्वास्थ्य निगरानी में योगदान करता है। आप हर बार मना कर सकते हैं।",
    aiDisclaimerTitle: "AI बीमारियों का निदान नहीं करता",
    aiDisclaimerText: "जागृति AI सामान्य, स्रोत-आधारित स्वास्थ्य जानकारी साझा करता है और आपको विश्वसनीय योजनाओं व सुविधाओं तक पहुंचाता है। यह कभी किसी स्थिति का निदान नहीं करता और किसी योग्य डॉक्टर की जगह नहीं लेता। आपातकाल में हमेशा 108 पर कॉल करें।",
    flowTitle: "एक प्रश्न सार्वजनिक स्वास्थ्य जागरूकता कैसे बनता है",
    flowStep1Title: "1. नागरिक पूछता है",
    flowStep1Text: "आप एक स्वास्थ्य प्रश्न पूछते हैं और निजी तौर पर एक आधारित उत्तर पाते हैं।",
    flowStep2Title: "2. गुमनाम संकेत",
    flowStep2Text: "यदि आप सहमति देते हैं, तो केवल एक गुमनाम विषय और मोटा स्थान एक समग्र गणना में जोड़ा जाता है — कभी आपकी पहचान नहीं।",
    flowStep3Title: "3. सरकारी जागरूकता",
    flowStep3Text: "स्वास्थ्य अधिकारी केवल समग्र, गुमनाम रुझान और मानव समीक्षा के लिए सांख्यिकीय अलर्ट देखते हैं — कभी व्यक्तिगत डेटा नहीं।",
  },
  or: {
    appName: "ଜାଗ୍ରତି AI",
    tagline: "AI-ଚାଳିତ ସ୍ୱାସ୍ଥ୍ୟ ସଚେତନତା ଏବଂ ପ୍ରାରମ୍ଭିକ ସଙ୍କେତ ପ୍ଲାଟଫର୍ମ",
    askQuestion: "ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ",
    askPlaceholder: "ଯେମିତି: ମୋର ଜ୍ୱର ଏବଂ ଗଣ୍ଠି ଯନ୍ତ୍ରଣା ଅଛି, ଏହା କଣ ହୋଇପାରେ?",
    send: "ପଚାରନ୍ତୁ",
    login: "ଲଗଇନ୍",
    register: "ପଞ୍ଜୀକରଣ",
    logout: "ଲଗଆଉଟ୍",
    dashboard: "ଡ୍ୟାସବୋର୍ଡ",
    schemes: "ସ୍ୱାସ୍ଥ୍ୟ ଯୋଜନା",
    myths: "ଭ୍ରମ ବନାମ ତଥ୍ୟ",
    nearby: "ନିକଟସ୍ଥ ସ୍ୱାସ୍ଥ୍ୟସେବା",
    govDashboard: "ସରକାରୀ ଡ୍ୟାସବୋର୍ଡ",
    consentPrompt: "ଆପଣ ଏହାକୁ ଅଜ୍ଞାତ ଭାବେ ସାର୍ବଜନୀନ ସ୍ୱାସ୍ଥ୍ୟ ଟ୍ରେଣ୍ଡ ମନିଟରିଂରେ ଯୋଗଦାନ କରିବାକୁ ଚାହାଁନ୍ତି କି?",
    consentYes: "ହଁ, ଅଜ୍ଞାତ ଭାବେ ଯୋଗଦାନ କରନ୍ତୁ",
    consentNo: "ନା ଧନ୍ୟବାଦ",
    disclaimerBanner: "ଜାଗ୍ରତି AI ସାଧାରଣ ସ୍ୱାସ୍ଥ୍ୟ ସୂଚନା ପ୍ରଦାନ କରେ, ଡାକ୍ତରୀ ନିଦାନ ନୁହେଁ। ଜରୁରୀକାଳୀନ ସ୍ଥିତିରେ 108 କୁ କଲ୍ କରନ୍ତୁ।",
    landingSubtitle: "ସାମୁଦାୟିକ ସ୍ୱାସ୍ଥ୍ୟ ସେଣ୍ଟିନେଲ",
    landingProblemTitle: "ସମସ୍ୟା",
    landingProblemText: "ସ୍ଥାନୀୟ ରୋଗ ପ୍ରକୋପର ପ୍ରାରମ୍ଭିକ ସଙ୍କେତ ପ୍ରାୟତଃ ସେତେବେଳେ ପର୍ଯ୍ୟନ୍ତ ଲକ୍ଷ୍ୟ ହୁଏ ନାହିଁ ଯେତେବେଳେ ସେଗୁଡ଼ିକ ଏକ ସାର୍ବଜନୀନ ସ୍ୱାସ୍ଥ୍ୟ ସମସ୍ୟା ପାଲଟିଯାଆନ୍ତି, କାରଣ ଦୈନନ୍ଦିନ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନଗୁଡ଼ିକୁ ଜିଲ୍ଲା-ସ୍ତରୀୟ ସଚେତନତା ସହିତ ଯୋଡ଼ିବାର କୌଣସି ସରଳ ଉପାୟ ନାହିଁ।",
    landingSolutionTitle: "ସମାଧାନ",
    landingSolutionText: "ଜାଗ୍ରତି AI ନାଗରିକମାନଙ୍କୁ ସେମାନଙ୍କ ନିଜ ଭାଷାରେ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ ପଚାରିବାକୁ ଏବଂ ଉତ୍ସ-ଆଧାରିତ ଉତ୍ତର ପାଇବାକୁ ଦେଇଥାଏ। ସ୍ପଷ୍ଟ ସହମତି ସହିତ, ଅଜ୍ଞାତ ବିଷୟ ସଙ୍କେତଗୁଡ଼ିକ ଏକ ପରିସାଂଖ୍ୟିକ ଅର୍ଲି ଅୱେୟାରନେସ ଇଞ୍ଜିନକୁ ଫିଡ୍ କରେ ଯାହା ଅସାଧାରଣ ପ୍ୟାଟର୍ନଗୁଡ଼ିକୁ ସ୍ୱାସ୍ଥ୍ୟ ଅଧିକାରୀଙ୍କ ସମୀକ୍ଷା ପାଇଁ ସାମନାକୁ ଆଣେ — କେବେହେଁ ନିଦାନ ନୁହେଁ, ସର୍ବଦା ମାନବ-ଯାଞ୍ଚିତ ସଙ୍କେତ।",
    askJagriti: "ଜାଗ୍ରତି AIକୁ ପଚାରନ୍ତୁ",
    exploreDisease: "ରୋଗ ସଚେତନତା ଦେଖନ୍ତୁ",
    forHealthOfficials: "ସ୍ୱାସ୍ଥ୍ୟ ଅଧିକାରୀଙ୍କ ପାଇଁ",
    privacyTitle: "ଆପଣଙ୍କ ଗୋପନୀୟତା ସୁରକ୍ଷିତ",
    privacyText: "ଆପଣ ପଚାରୁଥିବା ପ୍ରଶ୍ନଗୁଡ଼ିକ ଡିଫଲ୍ଟ ଭାବେ ବ୍ୟକ୍ତିଗତ। ଆପଣ ସ୍ପଷ୍ଟ ଭାବେ ସହମତି ଦେଲେ ହିଁ ଏକ ଅଜ୍ଞାତ ବିଷୟ ଟ୍ୟାଗ — କେବେହେଁ ଆପଣଙ୍କ ନାମ, ପ୍ରଶ୍ନ ପାଠ୍ୟ କିମ୍ବା ସଠିକ୍ ସ୍ଥାନ ନୁହେଁ — ସାର୍ବଜନୀନ ସ୍ୱାସ୍ଥ୍ୟ ମନିଟରିଂରେ ଯୋଗଦାନ କରେ। ଆପଣ ପ୍ରତ୍ୟେକ ଥର ମନା କରିପାରିବେ।",
    aiDisclaimerTitle: "AI ରୋଗ ନିଦାନ କରେ ନାହିଁ",
    aiDisclaimerText: "ଜାଗ୍ରତି AI ସାଧାରଣ, ଉତ୍ସ-ଆଧାରିତ ସ୍ୱାସ୍ଥ୍ୟ ସୂଚନା ପ୍ରଦାନ କରେ ଏବଂ ଆପଣଙ୍କୁ ବିଶ୍ୱସନୀୟ ଯୋଜନା ଓ ସୁବିଧା ପ୍ରତି ମାର୍ଗଦର୍ଶନ କରେ। ଏହା କେବେହେଁ କୌଣସି ଅବସ୍ଥାର ନିଦାନ କରେ ନାହିଁ ଏବଂ ଏକ ଯୋଗ୍ୟ ଡାକ୍ତରଙ୍କ ସ୍ଥାନ ନେଇପାରେ ନାହିଁ। ଜରୁରୀକାଳୀନ ସ୍ଥିତିରେ ସର୍ବଦା 108 କୁ କଲ୍ କରନ୍ତୁ।",
    flowTitle: "ଏକ ପ୍ରଶ୍ନ କିପରି ସାର୍ବଜନୀନ ସ୍ୱାସ୍ଥ୍ୟ ସଚେତନତା ପାଲଟେ",
    flowStep1Title: "୧. ନାଗରିକ ପଚାରନ୍ତି",
    flowStep1Text: "ଆପଣ ଏକ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ ପଚାରନ୍ତି ଏବଂ ବ୍ୟକ୍ତିଗତ ଭାବେ ଏକ ଆଧାରିତ ଉତ୍ତର ପାଆନ୍ତି।",
    flowStep2Title: "୨. ଅଜ୍ଞାତ ସଙ୍କେତ",
    flowStep2Text: "ଆପଣ ସହମତି ଦେଲେ, କେବଳ ଏକ ଅଜ୍ଞାତ ବିଷୟ ଏବଂ ମୋଟା ସ୍ଥାନ ଏକ ସାମଗ୍ରିକ ଗଣନାରେ ଯୋଡ଼ାଯାଏ — କେବେହେଁ ଆପଣଙ୍କ ପରିଚୟ ନୁହେଁ।",
    flowStep3Title: "୩. ସରକାରୀ ସଚେତନତା",
    flowStep3Text: "ସ୍ୱାସ୍ଥ୍ୟ ଅଧିକାରୀମାନେ କେବଳ ସାମଗ୍ରିକ, ଅଜ୍ଞାତ ରୁଝାନ ଏବଂ ମାନବ ସମୀକ୍ଷା ପାଇଁ ପରିସାଂଖ୍ୟିକ ଚେତାବନୀ ଦେଖନ୍ତି — କେବେହେଁ ବ୍ୟକ୍ତିଗତ ତଥ୍ୟ ନୁହେଁ।",
  },
};

interface I18nContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>((localStorage.getItem("jagriti_lang") as Lang) || "en");

  const changeLang = (l: Lang) => {
    localStorage.setItem("jagriti_lang", l);
    setLang(l);
  };

  const t = (key: string) => STRINGS[lang][key] ?? STRINGS.en[key] ?? key;

  return <I18nContext.Provider value={{ lang, setLang: changeLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
