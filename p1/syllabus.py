"""UGC NET Paper 1 (General Paper on Teaching & Research Aptitude): units and sub-topics.

Sub-topics follow the official NTA syllabus. Each sub-topic carries keywords used to
sort questions. A keyword can be a plain string (weight 1, or more for phrases) or a
(keyword, weight) pair. Edit freely: the classifier reads these lists at start-up.
"""

UNITS = {
    "U1": {
        "name": "Teaching Aptitude",
        "subtopics": {
            "U1.1": ("Concept, objectives & levels of teaching", [
                ("memory level", 4), ("understanding level", 4), ("reflective level", 4),
                ("levels of teaching", 4), "herbart", "morrison", ("hunt", 2), "objectives of teaching",
                ("teaching", 1), "maxims of teaching", ("bloom", 3), "taxonomy", "cognitive domain",
                "affective domain", "psychomotor"]),
            "U1.2": ("Learner characteristics", [
                ("learner", 2), "adolescent", "individual differences", "emotional", "cognitive development",
                "piaget", "vygotsky", "motivation", "intelligence", "learning style", "gifted",
                "slow learner", "adult learner", "andragogy", ("zone of proximal development", 7), ("scaffolding", 5), ("with the help of", 3), ("child", 2), ("reinforced", 5), ("reinforcement", 5), ("conditioning", 5), ("behaviourism", 5), ("behaviorism", 5), ("constructivism", 5), ("constructivist", 5), ("transmission model", 6), ("21st century skills", 6), ("21 century skills", 6), ("century skills", 5), ("learning", 1), ("students", 1), ("teacher", 2)]),
            "U1.3": ("Factors affecting teaching", [
                "factors affecting", "learning environment", "support material", "instructional facilities",
                "institutional", "classroom climate", "teacher effectiveness"]),
            "U1.4": ("Methods of teaching (teacher/learner-centred, offline/online)", [
                ("teacher-centred", 4), ("teacher centred", 4), ("teacher-centered", 4),
                ("learner-centred", 4), ("learner centred", 4), ("learner-centered", 4),
                ("lecture method", 3), "demonstration", ("project method", 3), "seminar", "tutorial",
                "brainstorming", ("flipped classroom", 4), ("blended learning", 4), "case method",
                "role play", ("swayam prabha", 4), ("swayamprabha", 4), ("mooc", 3), ("swayam", 3),
                "online teaching", "programmed instruction", "team teaching", "micro teaching",
                ("microteaching", 3), "heuristic", "problem solving method", "discussion method"]),
            "U1.5": ("Teaching support system (traditional, modern, ICT)", [
                ("teaching aids", 3), ("teaching aid", 3), ("audio-visual", 5), ("documentary", 4), ("audio only", 5), ("visual only", 5), ("instructional material", 5), ("material", 2), "chalk", "blackboard", "smart board",
                "overhead projector", "edusat", "multimedia", ("h5p", 6), ("content collaboration", 6), ("lms", 5),
                ("cms", 4), ("moodle", 6), ("learning management system", 6), ("e-content", 5)]),
            "U1.6": ("Evaluation systems (CBCS, CBT, innovations)", [
                ("evaluation", 2), ("formative", 3), ("summative", 3), ("diagnostic evaluation", 4),
                ("placement evaluation", 4), ("cbcs", 4), ("choice based credit", 4), ("credit", 1),
                ("grading", 2), ("grade point", 3), ("cgpa", 3), ("sgpa", 3), ("computer based test", 4),
                ("norm-referenced", 4), ("criterion-referenced", 4), ("norm referenced", 4),
                ("criterion referenced", 4), "continuous and comprehensive", ("cce", 3), "rubric",
                "open book", "assessment", "achievement test", "examination reform"]),
        },
    },
    "U2": {
        "name": "Research Aptitude",
        "subtopics": {
            "U2.1": ("Meaning, types & characteristics of research", [
                ("research", 2), ("fundamental research", 4), ("applied research", 4), ("action research", 4),
                ("basic research", 3), "pure research", "evaluation research", ("objectives of research", 3)]),
            "U2.2": ("Positivism & post-positivism; paradigms", [
                ("positivism", 4), ("positivist", 4), ("post-positivism", 4), ("postpositivism", 4),
                ("post positivism", 4), "paradigm", "phenomenology", "hermeneutics", "interpretivism",
                "auguste comte", "epistemology", "ontology"]),
            "U2.3": ("Methods: experimental, descriptive, historical, qualitative, quantitative", [
                ("experimental", 3), ("quasi-experimental", 4), ("ex post facto", 4), ("ex-post facto", 4),
                ("descriptive research", 4), ("historical research", 4), ("qualitative", 3),
                ("quantitative", 3), ("case study", 3), "ethnography", "survey", "grounded theory",
                "longitudinal", "cross-sectional", "correlational", ("ethnography", 6), ("ethnographic", 6), ("mixed method", 3), "triangulation",
                "control group", "independent variable", "dependent variable", ("variable", 2),
                ("sampling", 3), ("sample", 2), "random sampling", "stratified", "snowball", "purposive",
                "quota sampling", "cluster sampling", "population", "tool", "questionnaire",
                "interview schedule", "observation", "rating scale", "likert", "reliability", "validity", ("scale of measurement", 6),
                ("interval scale", 6), ("nominal scale", 6), ("ordinal scale", 6), ("ratio scale", 5), ("internal validity", 6),
                ("external validity", 6),
                "standard deviation", "mean", "median", "correlation", ("chi-square", 3), ("t-test", 3),
                "anova", "parametric", "non-parametric", "level of significance", "type i error",
                "type ii error", "content analysis", "focus group", "delphi", ("grounded theory", 7), ("quantitative research", 5), ("qualitative research", 5), ("research strategy", 5), ("standard normal", 6), ("normal distribution", 6), ("normal variate", 6), ("probability", 2), ("z-score", 5), ("statistical", 3), ("researcher", 2), ("first order correlation", 7), ("second order correlation", 7), ("correlation coefficient", 6)]),
            "U2.4": ("Steps of research & hypothesis", [
                ("hypothesis", 3), ("null hypothesis", 4), ("research problem", 4), ("review of literature", 4),
                ("literature review", 4), ("research design", 4), ("steps of research", 4),
                "formulation", "data collection", "generalisation", "generalization", "pilot study"]),
            "U2.5": ("Thesis & article writing, referencing styles", [
                ("thesis", 3), ("dissertation", 3), ("abstract", 3), ("bibliography", 4), ("references", 2),
                ("citation", 3), ("footnote", 3), ("apa", 4), ("mla", 4), ("chicago", 3), ("harvard", 3),
                ("ibid", 4), ("op. cit", 4), ("et al", 3), "peer review", "impact factor", "h-index",
                ("i10", 3), ("h-index", 6), ("h index", 6), ("citations", 4), "journal", "research paper", "monograph", "appendix", "keywords", "doi", "issn",
                "isbn", "conference", "symposium", "workshop", "seminar"]),
            "U2.6": ("ICT in research", [
                ("spss", 4), "software for research", "shodhganga", "shodhgangotri", ("inflibnet", 3),
                ("urkund", 4), ("ouriginal", 4), ("turnitin", 4), "reference manager", "zotero", "mendeley",
                "data analysis software", "online survey", "ugc-care", "ugc care"]),
            "U2.7": ("Research ethics", [
                ("research ethics", 4), ("ethics", 3), ("ethical", 3), ("plagiarism", 4), ("informed consent", 4),
                "confidentiality", "anonymity", "fabrication", "falsification", "predatory", "academic integrity",
                "conflict of interest", "self-plagiarism", "salami", ("hawthorne", 7), ("being studied", 5), ("participants", 3), ("respondents", 3)]),
        },
    },
    "U3": {
        "name": "Comprehension",
        "subtopics": {
            "U3.1": ("Passage-based questions", [
                ("read the passage", 8), ("the passage", 6), ("passage given", 8), ("according to the passage", 8),
                ("the author of the passage", 8), ("based on the passage", 8), ("the passage suggests", 8),
                ("as per the passage", 8), ("title of the passage", 8), ("in the passage", 6),
                ("according to the author", 6), ("the author", 3), ("the writer", 3)]),
        },
    },
    "U4": {
        "name": "Communication",
        "subtopics": {
            "U4.1": ("Meaning, types, characteristics & models", [
                ("communication", 3), "sender", "receiver", "encoding", "decoding", "channel", "feedback",
                "shannon", "weaver", "berlo", ("smcr", 4), "lasswell", "osgood", "schramm", "aristotle",
                "transactional", "linear model", "interactive model", ("transmission model", 6), ("adoption", 3), ("diffusion", 4), "downward", "upward", "horizontal",
                "lateral", ("grapevine", 4), "formal communication", "informal communication", ("mcluhan", 7), ("global village", 7), ("medium is the message", 7), ("opinion leader", 7), ("opinion leaders", 7), ("influence over decisions", 6), ("two-step flow", 7), ("diffusion of innovation", 7), ("communicator", 4)]),
            "U4.2": ("Effective communication: verbal, non-verbal, intercultural, group", [
                ("non-verbal", 4), ("nonverbal", 4), ("verbal", 2), "kinesics", "proxemics", "paralanguage",
                "chronemics", "haptics", "oculesics", "body language", "gesture", "eye contact",
                ("intercultural", 4), ("inter-cultural", 4), "group communication", "interpersonal",
                "intrapersonal", "listening", "empathy", "tone", ("community", 2), ("culture", 3), ("cultural", 3), ("patterned", 3)]),
            "U4.3": ("Barriers to communication", [
                ("barrier", 4), ("barriers", 4), "semantic", "noise", "physical barrier", "psychological barrier",
                "filtering", "information overload", "perception"]),
            "U4.4": ("Classroom communication", [
                ("classroom communication", 5), "teacher talk", "flanders", "classroom interaction"]),
            "U4.5": ("Mass media & society", [
                ("mass media", 4), ("mass communication", 4), "media", "newspaper", "television", "radio",
                "cinema", "social media", "agenda setting", "gatekeeping", "propaganda", "public opinion",
                "advertising", "press", "prasar bharati", "doordarshan", "akashvani", "community radio",
                "fake news", "censorship", "folk media", ("media channels", 6), ("elites", 4), ("ruling", 2)]),
        },
    },
    "U5": {
        "name": "Mathematical Reasoning & Aptitude",
        "subtopics": {
            "U5.13": ("Types of reasoning", [
                ("types of reasoning", 7), ("abductive", 6), ("abduction", 6), ("deductive reasoning", 6),
                ("inductive reasoning", 6), ("analogical reasoning", 6), ("mathematical reasoning", 6),
                ("reasoning", 2)]),
            "U5.1": ("Number series", [
                ("number series", 5), ("series", 3), ("next number", 5), ("next term", 5), ("missing number", 5),
                ("missing term", 5), ("wrong number", 5), ("wrong term", 5), ("replace the question mark", 5),
                ("in place of question mark", 5), ("in place of ?", 4)]),
            "U5.2": ("Letter & alphanumeric series", [
                ("letter series", 5), ("alphabet", 3), ("alphabetical", 3), ("letters", 2),
                ("alpha-numeric", 4), ("alphanumeric", 4)]),
            "U5.3": ("Coding-decoding", [
                ("coded as", 6), ("code language", 6), ("is written as", 4), ("coding", 4), ("decoding", 2),
                ("certain code", 6), ("in a code", 6), ("code for", 4)]),
            "U5.4": ("Relationships (blood relations, direction, ranking)", [
                ("blood relation", 5), ("father", 2), ("mother", 2), ("brother", 2), ("sister", 2),
                ("son", 1), ("daughter", 2), ("uncle", 2), ("aunt", 2), ("grandfather", 3), ("nephew", 3),
                ("niece", 3), ("husband", 2), ("wife", 2), ("related to", 3), ("north", 2), ("south", 2),
                ("east", 2), ("west", 2), ("facing", 2), ("rank", 2), ("position from", 3)]),
            "U5.5": ("Fractions, ratio & proportion", [
                ("ratio", 4), ("proportion", 4), ("fraction", 3), ("fractions", 5), ("partnership", 4), ("mixture", 4),
                ("alligation", 5), ("mean proportional", 5), ("third proportional", 5)]),
            "U5.6": ("Percentage", [
                ("percent", 3), ("percentage", 4), ("%", 2), ("increase by", 2), ("decrease by", 2)]),
            "U5.7": ("Profit, loss & discount", [
                ("profit", 4), ("loss", 3), ("cost price", 5), ("selling price", 5), ("marked price", 5),
                ("discount", 4), ("gain", 2)]),
            "U5.8": ("Simple & compound interest", [
                ("simple interest", 6), ("compound interest", 6), ("interest", 3), ("principal", 3),
                ("per annum", 4), ("compounded", 5), ("rate of interest", 5)]),
            "U5.9": ("Time, speed & distance", [
                ("speed", 4), ("distance", 3), ("km/h", 5), ("km/hr", 5), ("kmph", 5), ("m/s", 4), ("train", 4),
                ("boat", 4), ("stream", 3), ("upstream", 5), ("downstream", 5), ("race", 3), ("relative speed", 5)]),
            "U5.10": ("Time & work", [
                ("days to complete", 5), ("complete the work", 5), ("can do a", 4), ("can complete", 4),
                ("work in", 2), ("pipe", 4), ("cistern", 5), ("tank", 3), ("men can", 4), ("women can", 4)]),
            "U5.11": ("Averages & ages", [
                ("average", 4), ("years ago", 5), ("years hence", 5), ("age", 3), ("ages", 4), ("older", 3),
                ("younger", 3)]),
            "U5.12": ("Number system & other arithmetic", [
                ("lcm", 5), ("hcf", 5), ("l.c.m", 5), ("h.c.f", 5), ("divisible", 4), ("remainder", 4),
                ("prime", 3), ("sum of", 2), ("product of", 2), ("square root", 4), ("unit digit", 5),
                ("calendar", 4), ("clock", 4), ("leap year", 5), ("value of x", 6), ("values of x", 6), ("the value of", 3), ("minimum and maximum", 4), ("equation", 5), ("equations", 5), ("mathematical", 4), ("expression", 3), ("solution", 2), ("of a number", 5), ("the number", 2)]),
        },
    },
    "U6": {
        "name": "Logical Reasoning",
        "subtopics": {
            "U6.1": ("Argument structure; deductive vs inductive", [
                ("argument", 3), ("arguments", 3), ("premise", 4), ("premises", 4), ("conclusion", 3),
                ("deductive", 5), ("inductive", 5), ("deduction", 4), ("induction", 4), ("valid", 2),
                ("invalid", 3), ("sound", 2), ("cogent", 4), "strong", "weak", ("argument form", 5),
                ("modus ponens", 6), ("modus tollens", 6), ("affirming the consequent", 6),
                ("denying the antecedent", 6), ("disjunctive syllogism", 6), ("hypothetical syllogism", 6)]),
            "U6.2": ("Categorical propositions, mood & figure, square of opposition", [
                ("categorical", 5), ("proposition", 3), ("propositions", 3), ("square of opposition", 7),
                ("contradictory", 5), ("contradictories", 5), ("contrary", 5), ("contraries", 5),
                ("sub-contrary", 6), ("subcontrary", 6), ("sub contrary", 6), ("subaltern", 6),
                ("subalternation", 6), ("superaltern", 6), ("mood", 4), ("figure", 2), ("distributed", 5),
                ("distribution", 4), ("quality", 2), ("quantity", 2), ("universal affirmative", 6),
                ("universal negative", 6), ("particular affirmative", 6), ("particular negative", 6)]),
            "U6.3": ("Syllogisms & Venn diagrams", [
                ("syllogism", 6), ("venn", 6), ("venn diagram", 7), ("all", 0), ("some", 0),
                ("follows from", 3), ("definitely follow", 5), ("logically follow", 5), ("middle term", 6),
                ("major term", 6), ("minor term", 6), ("major premise", 6), ("minor premise", 6)]),
            "U6.4": ("Fallacies & uses of language; connotation/denotation", [
                ("fallacy", 6), ("fallacies", 6), ("ad hominem", 7), ("ad populum", 7), ("ad baculum", 7),
                ("ad misericordiam", 7), ("ad verecundiam", 7), ("ad ignorantiam", 7), ("straw man", 7),
                ("red herring", 7), ("begging the question", 7), ("petitio principii", 7), ("composition", 3),
                ("division", 2), ("equivocation", 6), ("amphiboly", 7), ("slippery slope", 7),
                ("hasty generalization", 7), ("false cause", 6), ("connotation", 6), ("denotation", 6),
                ("intension", 6), ("extension", 3), ("uses of language", 6), ("informative", 3),
                ("expressive", 3), ("directive", 3), ("definition", 2)]),
            "U6.5": ("Analogies", [("analogy", 6), ("analogical", 6), ("analogous", 5), ("is related to", 3),
                                   ("is to", 3)]),
            "U6.6": ("Indian logic: pramanas", [
                ("pramana", 7), ("pramanas", 7), ("pratyaksha", 7), ("pratyaksa", 7), ("anumana", 7),
                ("anumāna", 7), ("upamana", 7), ("shabda", 7), ("sabda", 7), ("śabda", 7), ("arthapatti", 7),
                ("arthāpatti", 7), ("anupalabdhi", 7), ("charvaka", 6), ("cārvāka", 6), ("nyaya", 6),
                ("nyāya", 6), ("mimamsa", 6), ("mīmāṃsā", 6), ("vaisesika", 6), ("vaisheshika", 6),
                ("samkhya", 6), ("sankhya", 6), ("advaita", 6), ("vedanta", 6), ("means of knowledge", 7),
                ("indian logic", 7), ("valid knowledge", 5), ("prama", 6)]),
            "U6.7": ("Indian logic: anumana structure, vyapti, hetvabhasa", [
                ("vyapti", 7), ("vyāpti", 7), ("hetvabhasa", 7), ("hetvābhāsa", 7), ("hetu", 6), ("paksha", 6),
                ("paksa", 6), ("sadhya", 6), ("sādhya", 6), ("pratijna", 7), ("pratijñā", 7), ("udaharana", 7),
                ("upanaya", 7), ("nigamana", 7), ("savyabhichara", 7), ("viruddha", 7), ("satpratipaksha", 7),
                ("asiddha", 7), ("badhita", 7), ("svarthanumana", 7), ("pararthanumana", 7), ("purvavat", 7),
                ("sheshavat", 7), ("samanyatodrishta", 7), ("five-membered", 6), ("five membered", 6)]),
        },
    },
    "U7": {
        "name": "Data Interpretation",
        "subtopics": {
            "U7.1": ("Data: sources, types & classification", [
                ("qualitative data", 6), ("quantitative data", 6), ("primary data", 6), ("secondary data", 6),
                ("nominal", 5), ("ordinal", 5), ("interval scale", 6), ("ratio scale", 6), ("discrete", 4),
                ("continuous", 3), ("categorical data", 6), ("time series", 5), ("cross-sectional data", 6),
                ("classification of data", 6), ("data", 1)]),
            "U7.2": ("Graphical representation & mapping", [
                ("histogram", 6), ("bar chart", 6), ("bar graph", 6), ("bar diagram", 6), ("pie chart", 6),
                ("pie diagram", 6), ("line graph", 6), ("line chart", 6), ("ogive", 6), ("frequency polygon", 6),
                ("scatter", 5), ("choropleth", 6), ("mapping of data", 6)]),
            "U7.3": ("Data interpretation sets (tables, charts)", [
                ("the following table", 8), ("given table", 7), ("table given", 7), ("table below", 7),
                ("the table", 5), ("study the", 3), ("the following data", 7), ("given data", 6),
                ("the chart", 5), ("the graph", 5), ("in the year", 3), ("production", 2), ("sales", 2),
                ("expenditure", 2), ("revenue", 2), ("total number of", 2), ("respectively", 1)]),
            "U7.4": ("Data & governance", [
                ("data and governance", 7), ("open government data", 7), ("data.gov.in", 7), ("big data", 5),
                ("data protection", 6), ("data privacy", 6), ("digital personal data", 7)]),
        },
    },
    "U8": {
        "name": "Information & Communication Technology (ICT)",
        "subtopics": {
            "U8.1": ("Abbreviations, terminology & computer basics", [
                ("ict", 4), ("computer", 3), ("hardware", 4), ("software", 4), ("cpu", 5), ("ram", 5), ("rom", 5),
                ("cache", 4), ("byte", 5), ("bytes", 5), ("bit", 3), ("bits", 3), ("kilobyte", 5), ("megabyte", 5),
                ("gigabyte", 5), ("terabyte", 5), ("petabyte", 5), ("binary", 5), ("hexadecimal", 5),
                ("octal", 5), ("decimal number", 4), ("operating system", 5), ("linux", 5), ("windows", 3),
                ("compiler", 5), ("interpreter", 4), ("ascii", 5), ("unicode", 5), ("usb", 5), ("bios", 5),
                ("full form", 4), ("stands for", 3), ("abbreviation", 4), ("pdf", 3), ("jpeg", 4), ("gif", 4),
                ("mp3", 4), ("spreadsheet", 4), ("excel", 4), ("word processor", 4), ("powerpoint", 4),
                ("keyboard", 4), ("shortcut", 3), ("ctrl", 5), ("storage", 3), ("ssd", 5), ("hard disk", 5),
                ("pen drive", 5), ("artificial intelligence", 4), ("cloud computing", 5), ("blockchain", 5),
                ("iot", 5), ("internet of things", 5), ("open-source", 6), ("open source", 6), ("javascript", 6), ("framework", 2), ("rfid", 7), ("radio frequency identification", 7), ("mail merge", 7), ("microsoft word", 6), ("ms-word", 6), ("ms-excel", 6), ("ms excel", 6), ("worksheet", 5), ("cell", 2), ("formula", 2), ("system software", 6), ("application software", 6), ("word processor", 5), ("notebook computer", 5), ("mini computer", 5), ("supercomputer", 5), ("mainframe", 5), ("simplex", 6), ("duplex", 6), ("half-duplex", 6), ("full-duplex", 6), ("serial", 3), ("parallel", 2), ("data transmission", 6)]),
            "U8.2": ("Internet, intranet, e-mail, conferencing", [
                ("internet", 4), ("intranet", 5), ("extranet", 5), ("e-mail", 5), ("email", 5), ("cc", 3),
                ("bcc", 5), ("url", 5), ("http", 5), ("https", 5), ("html", 5), ("www", 4), ("browser", 5),
                ("search engine", 5), ("ip address", 5), ("ipv4", 5), ("ipv6", 5), ("dns", 5), ("protocol", 4),
                ("tcp", 5), ("ftp", 5), ("smtp", 5), ("pop3", 5), ("imap", 5), ("lan", 5), ("wan", 5),
                ("router", 5), ("modem", 5), ("wi-fi", 5), ("wifi", 5), ("bluetooth", 5), ("bandwidth", 5),
                ("video conferencing", 5), ("audio conferencing", 5), ("webinar", 4), ("domain", 3), (".edu", 5),
                ("malware", 5), ("virus", 4), ("phishing", 5), ("firewall", 5), ("spam", 5), ("cookie", 5),
                ("encryption", 5), ("hacking", 5), ("worm", 4), ("trojan", 5), ("ransomware", 5), ("hacker", 6), ("hackers", 6), ("cracker", 5), ("computers", 3), ("cyber", 5)]),
            "U8.3": ("Digital initiatives in higher education", [
                ("swayam", 4), ("swayam prabha", 5), ("nptel", 6), ("e-pg pathshala", 7), ("epg pathshala", 7),
                ("ndli", 6), ("national digital library", 6), ("shodhganga", 5), ("vidwan", 6), ("e-shodh sindhu", 7),
                ("inflibnet", 4), ("abc", 3), ("academic bank of credits", 7), ("digilocker", 6),
                ("national academic depository", 7), ("diksha", 6), ("e-yantra", 7), ("virtual lab", 6),
                ("spoken tutorial", 7), ("samarth", 6), ("one nation one subscription", 7), ("pm e-vidya", 7)]),
            "U8.4": ("ICT & governance", [
                ("e-governance", 7), ("egovernance", 7), ("digital india", 6), ("aadhaar", 6), ("umang", 6),
                ("g2c", 7), ("g2b", 7), ("g2g", 7), ("mygov", 6), ("bhim", 5), ("upi", 5), ("common service centre", 6),
                ("e-office", 6), ("rti online", 6)]),
        },
    },
    "U9": {
        "name": "People, Development & Environment",
        "subtopics": {
            "U9.1": ("Development & environment: MDGs and SDGs", [
                ("sdg", 6), ("sdgs", 6), ("sustainable development goal", 7), ("mdg", 6), ("mdgs", 6),
                ("millennium development goal", 7), ("agenda 2030", 7), ("sustainable development", 5),
                ("brundtland", 7), ("our common future", 7), ("human development index", 6), ("hdi", 5)]),
            "U9.2": ("Human-environment interaction; anthropogenic impacts", [
                ("anthropogenic", 6), ("deforestation", 5), ("urbanisation", 4), ("urbanization", 4),
                ("land degradation", 5), ("desertification", 5), ("biodiversity", 5), ("ecosystem", 4),
                ("carrying capacity", 5), ("ecological footprint", 6), ("population", 2)]),
            "U9.3": ("Pollution, waste & health impacts", [
                ("pollution", 5), ("pollutant", 5), ("pollutants", 5), ("air quality", 6), ("aqi", 6),
                ("pm2.5", 6), ("pm 2.5", 6), ("pm10", 6), ("particulate", 6), ("sulphur dioxide", 5),
                ("nitrogen oxide", 5), ("carbon monoxide", 5), ("ozone", 3), ("smog", 5), ("acid rain", 6),
                ("bod", 5), ("biochemical oxygen demand", 6), ("eutrophication", 6), ("noise", 3), ("decibel", 5),
                ("waste", 4), ("e-waste", 6), ("biomedical waste", 6), ("hazardous waste", 6), ("solid waste", 6),
                ("plastic", 4), ("fluoride", 5), ("arsenic", 5), ("mercury", 4), ("lead", 2), ("minamata", 6),
                ("itai-itai", 6), ("health", 2), ("disease", 3), ("toxic", 4), ("kidney", 4), ("kidneys", 4), ("nephrotoxic", 6), ("landfill", 6), ("sanitary landfill", 7), ("organic pollutants", 6), ("acid rain", 6), ("sound limits", 6), ("db", 2)]),
            "U9.4": ("Climate change", [
                ("climate change", 6), ("global warming", 6), ("greenhouse", 6), ("ghg", 6), ("carbon dioxide", 4),
                ("methane", 5), ("nitrous oxide", 5), ("carbon footprint", 6), ("carbon credit", 6),
                ("net zero", 6), ("ipcc", 6), ("sea level", 5)]),
            "U9.5": ("Natural & energy resources", [
                ("renewable", 5), ("non-renewable", 5), ("solar", 4), ("wind energy", 6), ("wind power", 6),
                ("hydro", 4), ("geothermal", 6), ("biomass", 6), ("nuclear", 4), ("tidal", 5), ("fossil fuel", 5),
                ("coal", 4), ("energy", 2), ("installed capacity", 6), ("forest", 3), ("soil", 3), ("water resources", 5)]),
            "U9.6": ("Natural hazards & disaster mitigation", [
                ("disaster", 6), ("hazard", 5), ("earthquake", 6), ("tsunami", 6), ("cyclone", 6), ("flood", 5),
                ("drought", 5), ("landslide", 6), ("mitigation", 5), ("ndma", 6), ("sendai", 7), ("vulnerability", 4)]),
            "U9.7": ("Laws, plans & international agreements", [
                ("environment protection act", 7), ("environmental protection act", 7), ("1986", 2),
                ("napcc", 7), ("national action plan on climate change", 7), ("national mission", 5),
                ("montreal protocol", 7), ("kyoto protocol", 7), ("kyoto", 6), ("paris agreement", 7),
                ("rio summit", 7), ("earth summit", 7), ("stockholm", 6), ("convention on biological diversity", 7),
                ("cbd", 5), ("ramsar", 7), ("unfccc", 7), ("cop", 4), ("international solar alliance", 7),
                ("isa", 3), ("basel convention", 7), ("stockholm convention", 7), ("kigali", 7), ("nagoya", 7),
                ("cartagena", 7), ("ngt", 6), ("national green tribunal", 7), ("protocol", 2)]),
        },
    },
    "U10": {
        "name": "Higher Education System",
        "subtopics": {
            "U10.1": ("Higher learning in ancient India", [
                ("nalanda", 7), ("takshashila", 7), ("taxila", 7), ("vikramashila", 7), ("vikramshila", 7),
                ("valabhi", 7), ("odantapuri", 7), ("somapura", 7), ("jagaddala", 7), ("kanchi", 5),
                ("ancient india", 6), ("gurukul", 6), ("vedic", 5), ("buddhist", 4), ("pali", 4), ("xuanzang", 6),
                ("hiuen tsang", 6), ("fa-hien", 6), ("i-tsing", 6), ("upanayana", 6), ("samavartana", 6),
                ("ghatika", 6), ("agrahara", 6), ("matha", 4), ("vihara", 5), ("fort william college", 7), ("fort william", 6), ("wood's despatch", 7), ("macaulay", 5), ("hunter commission", 6), ("sadler commission", 6), ("calcutta madrasa", 6)]),
            "U10.2": ("Evolution of higher education & research after independence", [
                ("radhakrishnan commission", 7), ("university education commission", 7), ("kothari commission", 7),
                ("mudaliar commission", 7), ("1948", 3), ("1964", 3), ("1966", 3), ("yashpal", 7),
                ("national knowledge commission", 7), ("sam pitroda", 6), ("npe 1968", 7), ("npe 1986", 7),
                ("national policy on education", 7), ("programme of action", 6), ("1992", 2), ("iit", 4),
                ("iim", 4), ("central university", 5), ("first university", 5), ("1857", 4)]),
            "U10.3": ("Oriental, conventional & non-conventional programmes", [
                ("oriental", 6), ("sanskrit", 4), ("madrasa", 5), ("open university", 6), ("ignou", 6),
                ("distance education", 6), ("distance learning", 6), ("open and distance learning", 7),
                ("odl", 6), ("correspondence", 5), ("non-conventional", 6), ("conventional", 3)]),
            "U10.4": ("Professional, technical & skill-based education", [
                ("aicte", 7), ("ncte", 7), ("nmc", 6), ("medical council", 6), ("bar council", 6), ("pci", 4),
                ("coa", 4), ("icar", 6), ("vocational", 6), ("skill", 4), ("skill india", 6), ("nsqf", 7),
                ("apprenticeship", 6), ("polytechnic", 6), ("iti", 4), ("technical education", 6),
                ("professional education", 6)]),
            "U10.5": ("Value education & environmental education", [
                ("value education", 7), ("values", 1), ("human values", 6), ("moral", 4), ("ethics", 2),
                ("environmental education", 7), ("environmental awareness", 6), ("peace education", 6),
                ("constitutional values", 6), ("fundamental duties", 6), ("preamble", 5), ("panchakosha", 7), ("kosha", 6), ("annamaya", 7), ("patanjali", 5), ("yoga", 4), ("ashtanga", 5), ("holistic development", 5), ("universal human values", 6)]),
            "U10.6": ("Policies, governance & administration", [
                ("ugc", 6), ("naac", 7), ("nirf", 7), ("nba", 6), ("nep", 6), ("nep 2020", 7),
                ("national education policy", 7), ("heci", 7), ("higher education commission of india", 7),
                ("rusa", 7), ("institutions of eminence", 7), ("institution of eminence", 7), ("ioe", 6),
                ("deemed university", 7), ("deemed to be university", 7), ("state university", 6),
                ("private university", 6), ("autonomous college", 7), ("autonomy", 5), ("accreditation", 6),
                ("ranking", 4), ("governance", 5), ("vice-chancellor", 6), ("vice chancellor", 6),
                ("chancellor", 5), ("visitor", 5), ("executive council", 6), ("academic council", 6),
                ("court", 2), ("senate", 4), ("syndicate", 4), ("board of studies", 6), ("article", 3),
                ("constitution", 4), ("concurrent list", 7), ("union list", 7), ("state list", 7),
                ("42nd amendment", 7), ("entry 66", 7), ("aishe", 7), ("gross enrolment ratio", 7), ("ger", 5),
                ("multiple entry", 6), ("academic bank", 6), ("four-year", 4), ("nhec", 7), ("ncrf", 7),
                ("nheqf", 7), ("parakh", 6), ("hecc", 4), ("pm-usha", 7), ("pm usha", 7), ("planning commission", 7), ("niti aayog", 7), ("statutory body", 6), ("constitutional body", 6), ("advisory body", 5), ("executive body", 5), ("entry eligibility", 6), ("education institutions", 5), ("educational institutions", 5), ("higher education institutions", 6), ("national coordinator", 6), ("college", 2), ("diploma", 3), ("doctoral", 3), ("ph.d", 4), ("rpwd", 6), ("rte act", 6), ("rci", 5), ("pwd act", 6), ("university", 3)]),
        },
    },
}

# Every unit also gets an "Other topics" bucket for questions whose unit is known (e.g. from the
# paper's 5-question block) but whose topic the keywords can't tell.
for _uid, _u in UNITS.items():
    _u["subtopics"][f"{_uid}.99"] = ("Other topics in this unit", [])

# The official syllabus: "Five questions each carrying 2 marks are to be set from each Module."
QUESTIONS_PER_UNIT = 5

PASS_FRACTION_HINT = (
    "JRF cut-offs change every session and by category. Check the latest NTA cut-off notice "
    "and set your own target in the app."
)


def unit_name(uid: str | None) -> str:
    if not uid:
        return "Needs review"
    return UNITS[uid]["name"] if uid in UNITS else uid


def subtopic_name(sid: str | None) -> str:
    if not sid:
        return "General"
    uid = sid.split(".")[0]
    return UNITS.get(uid, {}).get("subtopics", {}).get(sid, (sid,))[0]


def unit_label(uid: str | None) -> str:
    return f"{uid} · {unit_name(uid)}" if uid else "Needs review"
