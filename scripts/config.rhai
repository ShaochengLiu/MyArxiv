// Paper types worth prioritizing in multimodal and omni-modal research.
let titles_type = [
    "Benchmark", "Dataset", "Survey", "Review", "Overview", "Evaluation"
];

// Multimodal/omni-modal model families and representative systems.
let titles_model = [
    "Multimodal Large Language Model", "Large Multimodal Model",
    "Multimodal Foundation Model", "Multimodal LLM", "MLLM", "LMM",
    "Vision-Language Model", "Vision Language Model",
    "Audio-Language Model", "Audio Language Model",
    "Video-Language Model", "Video Language Model",
    "Omni-modal Large Language Model", "Omnimodal Foundation Model",
    "Any-to-Any Multimodal", "Unified Multimodal", "Native Multimodal",
    "Omnimodal", "Omni-modal", "Omni Model", "OmniModel", "Any-to-Any",
    "LLaVA", "InternVL", "Qwen2[.]5-Omni", "Qwen2[.]5-VL",
    "Qwen-VL", "Qwen-Omni", "MiniCPM-o",
    "GPT-4o", "Gemini", "Janus", "Chameleon", "Emu3",
    "NExT-GPT", "AnyGPT", "ImageBind"
];

// Core capabilities and training/alignment techniques.
let titles_method = [
    "Multimodal Reasoning", "Multimodal Understanding",
    "Multimodal Generation", "Multimodal Alignment",
    "Multimodal Instruction Tuning", "Multimodal Pretraining",
    "Interleaved Multimodal", "Cross-Modal Alignment", "Cross-Modal",
    "Modality Alignment", "Unified Tokenization", "Multimodal Tokenizer",
    "Vision-Language", "Audio-Visual", "Audio-Language",
    "Video-Language", "Speech-Language", "Image-Text",
    "Speech Understanding", "Audio Understanding", "Video Understanding"
];
let titles =  titles_model + titles_method + titles_type;
let authors_array = ["Yann LeCun", "Geoffrey Hinton", "Yoshua Bengio"];

let conferences = [
    // AI
    "AAAI", "AAMAS", "ACM MM", "AISTATS", "ALT", "CEC", "ECAI", "FUZZ IEEE", "GECCO", "ICANN", "ICAPS", "ICCBR", "ICONIP", "ICRA", "ICTAI", "IJCAI", "IJCNN", "IROS", "KR", "KSEM", "SIGGRAPH", "STOC", "UAI", "PPSN", "PRICAI", "TAAI",
    // CV
    "3DV", "ACCV", "ACM MM", "BMVC", "CVPR", "ECCV", "ICCV", "ICDAR", "ICIP", "ICME", "ICPR", "IEEE VIS", "MICCAI", "SIGGRAPH", "WACV",
    // DM
    "AKBC", "APWeb", "CIKM", "DASFAA", "ECML-PKDD", "ICDE", "ICDM", "ICDT", "KDD", "LREC", "MDM", "PAKDD", "PODS", "RecSys", "SDM", "SIGMOD", "VLDB", "WSDM", "WWW", "EDBT", "CIDR",
    // IR
    "ECIR", "ESWC", "ICMR", "ICTIR", "ISWC", "SIGIR",
    // ML
    "ACML", "AISTATS", "ECML", "ICLR", "ICML", "ML4H", "NeurIPS", "NIPS", "UAI",
    // NLP
    "AACL", "ACL", "CCL", "COLING", "COLT", "CoNLL", "EACL", "EMNLP", "ICASSP", "ICDAR", "ICONIP", "INTERSPEECH", "LREC", "NAACL", "NLPCC", "RepL4NLP", "SIGDIAL", "SemEval", "WANLP", "WASSA", "WOAH",
    // Arch
    "ASPLOS", "ATC", "DATE", "EuroSys", "FAST", "HPCA", "ISCA", "MICRO", "PPoPP", "SC", "SoCC",
    // System
    "FSE/ESEC", "ICSE", "ISSTA", "OSDI", "SOSP",
    // Security
    "ACSA", "AsiaCCS", "CCS", "DSN", "ESORICS", "EuroS&P", "ICICS", "NDSS", "RAID", "SP", "USENIX Security"
];

let start = conferences.shift();
let conferences_rg = conferences.reduce(|sum, v| sum + "|" + v, start);
let conferences_rg = "(" + conferences_rg + ")([\\s'-]*\\d+)?";

let start = titles.shift();
let title_rg = titles.reduce(|sum, v| sum + "|" + v, start);

let start = authors_array.shift();
let authors_rg = authors_array.reduce(|sum, v| sum + "|" + v, start);

export title_rg;
export authors_rg;
export conferences_rg;
