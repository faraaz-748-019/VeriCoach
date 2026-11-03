import type { LanguageCode } from '../types/api';

export interface Translations {
  appName: string;
  tagline: string;
  selectLanguage: string;
  english: string;
  hindi: string;
  telugu: string;
  welcomeTitle: string;
  welcomeSubtitle: string;
  exampleQueriesTitle: string;
  exampleQueries: string[];
  inputPlaceholder: string;
  send: string;
  sending: string;
  loadingMessage: string;
  sourcesTitle: string;
  sourcesDescription: string;
  viewSources: string;
  hideSources: string;
  noSources: string;
  relevanceScore: string;
  thumbsUp: string;
  thumbsDown: string;
  feedbackSuccess: string;
  feedbackError: string;
  offlineBannerTitle: string;
  offlineBannerDesc: string;
  errorBannerTitle: string;
  dismiss: string;
  retry: string;
  refusedBadge: string;
  settingsTitle: string;
  backendUrlLabel: string;
  backendUrlHelp: string;
  apiKeyLabel: string;
  saveSettings: string;
  settingsSaved: string;
  resetDefault: string;
  disclaimer: string;
}

export const TRANSLATIONS: Record<LanguageCode, Translations> = {
  en: {
    appName: 'VeriCoach',
    tagline: 'Multilingual Personal Finance Assistant',
    selectLanguage: 'Select Language',
    english: 'English',
    hindi: 'हिंदी (Hindi)',
    telugu: 'తెలుగు (Telugu)',
    welcomeTitle: 'Hello! How can I help with your finances today?',
    welcomeSubtitle: 'Ask questions about UPI safety, KYC guidelines, mutual funds, budgeting, credit scores, or cyber fraud prevention.',
    exampleQueriesTitle: 'Try asking:',
    exampleQueries: [
      'Do I need to enter my UPI PIN to receive money?',
      'What documents are accepted for KYC verification?',
      'How does the 50/30/20 budgeting rule work?',
      'What should I do immediately if I suspect a cyber financial scam?',
    ],
    inputPlaceholder: 'Type your financial question in English, Hindi, or Telugu...',
    send: 'Send',
    sending: 'Sending...',
    loadingMessage: 'Analyzing verified financial guidelines and generating response...',
    sourcesTitle: 'Verified Sources & Citations',
    sourcesDescription: 'Educational sources retrieved from the knowledge base grounding this answer:',
    viewSources: 'View Citations',
    hideSources: 'Hide Citations',
    noSources: 'No specific citations retrieved for this response.',
    relevanceScore: 'Match Score',
    thumbsUp: 'Helpful answer',
    thumbsDown: 'Not helpful',
    feedbackSuccess: 'Thank you for your feedback!',
    feedbackError: 'Could not record feedback',
    offlineBannerTitle: 'You are currently offline',
    offlineBannerDesc: 'Please check your internet connection. Some features may not work until connection is restored.',
    errorBannerTitle: 'Request Failed',
    dismiss: 'Dismiss',
    retry: 'Retry',
    refusedBadge: 'Safety Advisory Refusal',
    settingsTitle: 'Connection & Settings',
    backendUrlLabel: 'Backend API Base URL',
    backendUrlHelp: 'Use http://10.0.2.2:8000 for Android emulator, or http://localhost:8000 for web.',
    apiKeyLabel: 'API Key (Optional)',
    saveSettings: 'Save Settings',
    settingsSaved: 'Settings saved successfully!',
    resetDefault: 'Reset to Default',
    disclaimer: 'Educational information only. Not personalized financial or investment advice.',
  },
  hi: {
    appName: 'वेरीकोच (VeriCoach)',
    tagline: 'बहुभाषी व्यक्तिगत वित्त सहायक',
    selectLanguage: 'भाषा चुनें',
    english: 'English',
    hindi: 'हिंदी (Hindi)',
    telugu: 'తెలుగు (Telugu)',
    welcomeTitle: 'नमस्ते! मैं आपकी वित्तीय सहायता कैसे कर सकता हूँ?',
    welcomeSubtitle: 'यूपीआई सुरक्षा, केवाईसी दिशानिर्देश, म्यूचुअल फंड, बजट नियम, सिबिल स्कोर या साइबर धोखाधड़ी से जुड़े सवाल पूछें।',
    exampleQueriesTitle: 'कुछ उदाहरण प्रश्न:',
    exampleQueries: [
      'क्या पैसे प्राप्त करने के लिए मुझे यूपीआई पिन दर्ज करने की आवश्यकता है?',
      'केवाईसी सत्यापन के लिए कौन से दस्तावेज मान्य हैं?',
      '50/30/20 बजट नियम कैसे काम करता है?',
      'वित्तीय धोखाधड़ी होने पर तुरंत क्या कदम उठाने चाहिए?',
    ],
    inputPlaceholder: 'अपना वित्तीय प्रश्न यहाँ लिखें...',
    send: 'भेजें',
    sending: 'भेज रहे हैं...',
    loadingMessage: 'प्रमाणित वित्तीय जानकारी की जांच और उत्तर तैयार किया जा रहा है...',
    sourcesTitle: 'प्रमाणित संदर्भ एवं स्रोत (Citations)',
    sourcesDescription: 'इस उत्तर के लिए ज्ञानकोष से प्राप्त सत्यापित स्रोत:',
    viewSources: 'स्रोत देखें',
    hideSources: 'स्रोत छिपाएं',
    noSources: 'इस उत्तर के लिए कोई संदर्भ उपलब्ध नहीं है।',
    relevanceScore: 'प्रासंगिकता स्कोर',
    thumbsUp: 'उपयोगी उत्तर',
    thumbsDown: 'अनुपयोगी उत्तर',
    feedbackSuccess: 'आपकी प्रतिक्रिया के लिए धन्यवाद!',
    feedbackError: 'प्रतिक्रिया दर्ज नहीं हो सकी',
    offlineBannerTitle: 'आप ऑफलाइन हैं',
    offlineBannerDesc: 'कृपया अपना इंटरनेट कनेक्शन जांचें। कनेक्शन बहाल होने तक कुछ सुविधाएं काम नहीं करेंगी।',
    errorBannerTitle: 'अनुरोध विफल रहा',
    dismiss: 'खारिज करें',
    retry: 'पुनः प्रयास करें',
    refusedBadge: 'सुरक्षा नियम अस्वीकृति',
    settingsTitle: 'कनेक्शन एवं सेटिंग्स',
    backendUrlLabel: 'बैकएंड एपीआई यूआरएल',
    backendUrlHelp: 'एंड्रॉइड एमुलेटर के लिए http://10.0.2.2:8000 और वेब के लिए http://localhost:8000 का उपयोग करें।',
    apiKeyLabel: 'एपीआई कुंजी (वैकल्पिक)',
    saveSettings: 'सहेजें',
    settingsSaved: 'सेटिंग्स सफलतापूर्वक सहेजी गईं!',
    resetDefault: 'डिफ़ॉल्ट पर रीसेट करें',
    disclaimer: 'केवल शैक्षणिक उद्देश्य हेतु। यह व्यक्तिगत वित्तीय सलाह नहीं है।',
  },
  te: {
    appName: 'వెరికోచ్ (VeriCoach)',
    tagline: 'బహుభాషా వ్యక్తిగత ఆర్థిక సహాయకుడు',
    selectLanguage: 'భాషను ఎంచుకోండి',
    english: 'English',
    hindi: 'हिंदी (Hindi)',
    telugu: 'తెలుగు (Telugu)',
    welcomeTitle: 'నమస్కారం! నేడు మీ ఆర్థిక విషయాలలో ఎలా సహాయపడగలను?',
    welcomeSubtitle: 'యూపీఐ భద్రత, కేవైసీ నియమాలు, మ్యూచువల్ ఫండ్స్, బడ్జెట్ ప్రణాళిక, సైబర్ మోసాల నివారణ గురించిన ప్రశ్నలు అడగండి.',
    exampleQueriesTitle: 'ఉదాహరణ ప్రశ్నలు:',
    exampleQueries: [
      'డబ్బులు తీసుకోవడానికి యూపీఐ పిన్ నమోదు చేయాలా?',
      'కేవైసీ ధృవీకరణకు ఏ ఏ పత్రాలు అవసరం?',
      '50/30/20 బడ్జెట్ నియమం ఎలా పనిచేస్తుంది?',
      'ఆర్థిక మోసం జరిగినప్పుడు తక్షణమే ఏమి చేయాలి?',
    ],
    inputPlaceholder: 'మీ ఆర్థిక ప్రశ్నను ఇక్కడ టైప్ చేయండి...',
    send: 'పంపు',
    sending: 'పంపిస్తోంది...',
    loadingMessage: 'ప్రామాణిక సమాచారాన్ని పరిశీలించి సమాధానాన్ని సిద్ధం చేస్తోంది...',
    sourcesTitle: 'ధృవీకరించబడిన ఆధారాలు మరియు మూలాలు (Citations)',
    sourcesDescription: 'ఈ సమాధానం కోసం ప్రామాణిక డేటాబేస్ నుండి పొందిన ఆధారాలు:',
    viewSources: 'ఆధారాలు చూడండి',
    hideSources: 'ఆధారాలు దాచు',
    noSources: 'ఈ సమాధానానికి ఎటువంటి ఆధారాలు లభించలేదు.',
    relevanceScore: 'ప్రాముఖ్యత స్కోరు',
    thumbsUp: 'ఉపయోగకరమైన సమాధానం',
    thumbsDown: 'ఉపయోగపడలేదు',
    feedbackSuccess: 'మీ అభిప్రాయానికి ధన్యవాదాలు!',
    feedbackError: 'అభిప్రాయాన్ని నమోదు చేయలేకపోయాము',
    offlineBannerTitle: 'మీరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉన్నారు',
    offlineBannerDesc: 'దయచేసి మీ ఇంటర్నెట్ కనెక్షన్‌ను తనిఖీ చేయండి. కనెక్షన్ పునరుద్ధరించబడే వరకు కొన్ని ఫీచర్లు పనిచేయవు.',
    errorBannerTitle: 'అభ్యర్థన విఫలమైంది',
    dismiss: 'తీసివేయి',
    retry: 'మళ్లీ ప్రయత్నించండి',
    refusedBadge: 'భద్రతా నిబంధనల తిరస్కరణ',
    settingsTitle: 'కనెక్షన్ మరియు సెట్టింగులు',
    backendUrlLabel: 'బ్యాకెండ్ API URL',
    backendUrlHelp: 'Android ఎమ్యులేటర్ కోసం http://10.0.2.2:8000, వెబ్ కోసం http://localhost:8000 ఉపయోగించండి.',
    apiKeyLabel: 'API కీ (ఐచ్ఛికం)',
    saveSettings: 'భద్రపరుచు',
    settingsSaved: 'సెట్టింగ్‌లు విజయవంతంగా భద్రపరచబడ్డాయి!',
    resetDefault: 'డిఫాల్ట్‌కు రీసెట్ చేయండి',
    disclaimer: 'కేవలం విద్యా ప్రయోజనాల కోసం మాత్రమే. ఇది వ్యక్తిగత ఆర్థిక సలహా కాదు.',
  },
};
