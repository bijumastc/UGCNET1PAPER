"""Learning module content: unit overviews, beginner-to-advanced primers, resources.

Primers teach the method from zero. They contain no practice questions: practice always
comes from the user's own past papers. Each primer has:
  zero      - the idea in plain words, assuming no background
  method    - the steps to follow in the exam
  traps     - where candidates usually lose the mark
  scale_up  - what to master next once the basics are steady
"""

UNIT_GUIDES = {
    "U1": {
        "overview": "How teaching works in higher education: its aims and levels, who the learner is, what "
                    "affects teaching, teaching methods (including online ones such as SWAYAM and MOOCs), "
                    "support systems, and how learning is evaluated (CBCS, computer-based tests).",
        "watch": ["Levels of teaching and their proponents (memory – Herbart, understanding – Morrison, "
                  "reflective – Hunt)", "Teacher-centred vs learner-centred methods",
                  "Formative vs summative vs diagnostic evaluation", "CBCS terms (credits, grade points, SGPA/CGPA)",
                  "Online platforms: SWAYAM, SWAYAM Prabha, MOOCs"],
        "resources": [
            ("NTA Paper 1 syllabus (official)", "https://ugcnet.nta.ac.in"),
            ("IGNOU eGyanKosh: education and teaching material (free)", "https://egyankosh.ac.in"),
            ("SWAYAM courses on pedagogy and teaching in higher education", "https://swayam.gov.in"),
            ("UGC guidelines on CBCS and learning outcomes", "https://www.ugc.gov.in"),
        ],
    },
    "U2": {
        "overview": "What research is and its types, the positivist and post-positivist approaches, research "
                    "methods, the steps of research, writing theses and articles with correct referencing, "
                    "using ICT in research, and research ethics.",
        "watch": ["Types of research: fundamental, applied, action", "Probability vs non-probability sampling",
                  "Hypothesis types (null, alternative, directional)", "Steps of research in order",
                  "Referencing styles (APA, MLA) and terms like ibid., op. cit., et al.",
                  "Plagiarism and research ethics, including UGC's 2018 plagiarism regulations"],
        "resources": [
            ("C. R. Kothari & G. Garg, Research Methodology: Methods and Techniques (book)", None),
            ("Ranjit Kumar, Research Methodology: A Step-by-Step Guide for Beginners (book)", None),
            ("Shodhganga: Indian theses repository (INFLIBNET)", "https://shodhganga.inflibnet.ac.in"),
            ("UGC Regulations on Academic Integrity and Prevention of Plagiarism, 2018", "https://www.ugc.gov.in"),
        ],
    },
    "U3": {
        "overview": "A passage followed by about five questions. It tests whether you can find the main idea, "
                    "the author's view, a stated fact, an inference, or a suitable title, using only the passage.",
        "watch": ["Main idea / suitable title", "What the author implies (inference)", "What is stated vs not stated",
                  "Meaning of a word or phrase in context"],
        "resources": [
            ("Daily habit: read one newspaper editorial and summarise it in two lines", None),
            ("Your own past-paper passages (Practice → Comprehension)", None),
        ],
        "primers": {
            "U3.1": {
                "zero": "Every question can be answered from the passage alone. Your job is to find the sentence "
                        "that answers it, not to bring in what you know.",
                "method": ["Skim the passage once for its topic and the author's attitude (for, against, neutral).",
                           "Read the question and note its type: main idea, fact, inference, or vocabulary.",
                           "Go back to the passage and find the exact lines.",
                           "Remove options that are too broad, too narrow, or not mentioned."],
                "traps": ["Choosing an option that is true in real life but not said in the passage.",
                          "Picking a detail as the 'main idea'.",
                          "Missing words like 'only', 'always', 'never' that make an option too extreme."],
                "scale_up": "Time yourself: aim for the whole passage set in about 7–8 minutes.",
            },
        },
    },
    "U4": {
        "overview": "Meaning, types and characteristics of communication; effective verbal, non-verbal, "
                    "intercultural and group communication; classroom communication; barriers; mass media "
                    "and society.",
        "watch": ["Elements of the communication process (sender, message, channel, receiver, feedback)",
                  "Models: Aristotle, Lasswell, Shannon–Weaver, Berlo's SMCR, Schramm",
                  "Types of non-verbal cues (kinesics, proxemics, paralanguage, chronemics)",
                  "Kinds of barriers (semantic, physical, psychological, cultural)",
                  "Functions and effects of mass media (agenda setting, gatekeeping)"],
        "resources": [
            ("IGNOU eGyanKosh: communication and mass communication material", "https://egyankosh.ac.in"),
            ("SWAYAM / e-PG Pathshala modules on communication", "https://epgp.inflibnet.ac.in"),
        ],
    },
    "U5": {
        "overview": "Number and letter series, coding-decoding, relationships, and everyday arithmetic: "
                    "fractions, ratio, percentage, profit and loss, interest, averages, time and distance. "
                    "All of it is school maths; the skill being tested is speed and method.",
        "watch": ["Number series (differences, squares, alternate terms)", "Letter series (alphabet positions)",
                  "Coding-decoding (letter shifts)", "Percentage and ratio", "Simple vs compound interest",
                  "Speed–time–distance"],
        "resources": [
            ("NCERT Mathematics, Classes 6–10 (free PDFs)", "https://ncert.nic.in/textbook.php"),
            ("R. S. Aggarwal, Quantitative Aptitude (book)", None),
            ("Khan Academy: arithmetic, ratios, percentages (free)", "https://www.khanacademy.org"),
        ],
        "primers": {
            "U5.13": {
                "zero": "Reasoning means reaching a conclusion from information. The syllabus asks you to tell the "
                        "main types apart.",
                "method": ["Deductive: from a general rule to a certain conclusion (All metals expand when heated; "
                           "iron is a metal; so iron expands). If the premises are true, the conclusion must be true.",
                           "Inductive: from observed cases to a probable general rule (every crow seen so far is black, "
                           "so all crows are probably black). The conclusion can be wrong.",
                           "Abductive: inference to the best explanation (the grass is wet, so it probably rained).",
                           "Analogical: two things are alike in some ways, so probably alike in another.",
                           "Mathematical reasoning in this unit means series, codes, relationships and arithmetic: "
                           "each follows a rule you find and then apply."],
                "traps": ["Calling any argument with 'all' deductive: 'All swans I have seen are white, so all swans "
                          "are white' is inductive.", "Treating a strong inductive argument as certain."],
                "scale_up": "Go on to Unit 6 for validity, soundness and argument forms in detail.",
            },
            "U5.1": {
                "zero": "A number series is a list of numbers made by a hidden rule. You find the rule by looking "
                        "at how each number changes into the next.",
                "method": ["Write the difference between each pair of neighbours under the series.",
                           "If the differences are equal → add that difference (arithmetic series).",
                           "If not, take differences of the differences. Equal second differences → rule found.",
                           "Still nothing? Divide neighbours: a constant ratio means multiply (geometric series).",
                           "Check for squares (1, 4, 9, 16…), cubes (1, 8, 27…), or n² ± something.",
                           "Check alternate terms (1st, 3rd, 5th… and 2nd, 4th, 6th…) as two separate series.",
                           "Check mixed rules such as ×2 +1, ×3 −1, or ×1 +1, ×2 +2, ×3 +3."],
                "traps": ["Stopping at the first rule that fits three numbers; test it on ALL numbers.",
                          "Forgetting the series can run two rules at alternate positions."],
                "scale_up": "Learn squares to 30² and cubes to 15³ by heart; most 'hard' series use them. Then "
                            "practise 'find the wrong term' questions, where one number breaks the rule.",
            },
            "U5.2": {
                "zero": "Letters become numbers: A=1, B=2 … Z=26. A letter series is just a number series "
                        "written in letters.",
                "method": ["Write each letter's position number under it (EJOTY → 5 10 15 20 25).",
                           "For groups like 'AZ, BY, CX', handle each position in the group separately.",
                           "Find the rule exactly as in number series.",
                           "If you pass 26, wrap around: 27 → A, 28 → B."],
                "traps": ["Counting positions slowly. Memorise the anchor 'EJOTY' (5, 10, 15, 20, 25).",
                          "Forgetting the reverse alphabet: Z=1, Y=2 … (opposite pairs add to 27: A–Z, B–Y)."],
                "scale_up": "Practise mixed alphanumeric series, where letters and numbers move by different rules.",
            },
            "U5.3": {
                "zero": "In coding-decoding, a word is turned into a code by a fixed rule, such as moving each "
                        "letter forward by one.",
                "method": ["Write the word and its code letter by letter, one under the other.",
                           "Write the position number of each letter and find the change (+1, −2, reversed…).",
                           "Check whether the rule is the same for every letter or changes by position.",
                           "Apply the same rule to the new word."],
                "traps": ["Assuming the same shift for every letter when it actually alternates (+1, −1, …).",
                          "Missing that the word was reversed first."],
                "scale_up": "Move on to number coding (letters → numbers) and sentence coding, where you match "
                            "common words between two coded sentences.",
            },
            "U5.4": {
                "zero": "Relationship questions ask how two people are related, or where someone ends up after "
                        "moving in given directions.",
                "method": ["Draw it. For family: use + for male, − for female, vertical lines for generations, "
                           "horizontal lines for siblings, = for married couples.",
                           "For directions: draw North at the top and track every turn on paper.",
                           "Read the statement again and check your drawing against each phrase."],
                "traps": ["Assuming gender from a name.", "Mixing up left and right turns after facing south."],
                "scale_up": "Use Pythagoras for the straight-line distance in direction questions (3-4-5, 5-12-13).",
            },
            "U5.5": {
                "zero": "A ratio compares two amounts. 2:3 means for every 2 of the first there are 3 of the "
                        "second, so 5 parts in total.",
                "method": ["Add the ratio parts to get the total number of parts.",
                           "Value of one part = total amount ÷ total parts.",
                           "Multiply back to get each share.",
                           "To combine A:B and B:C, make the B values equal first."],
                "traps": ["Dividing by one part instead of the total parts.", "Not making the common term equal."],
                "scale_up": "Learn alligation for mixtures: (dearer − mean) : (mean − cheaper) gives the mixing ratio.",
            },
            "U5.6": {
                "zero": "Percent means 'out of 100'. 20% of 150 = 20/100 × 150 = 30.",
                "method": ["Percentage change = (new − old) ÷ old × 100. Always divide by the OLD value.",
                           "Use fractions to go faster: 10% = 1/10, 12.5% = 1/8, 20% = 1/5, 25% = 1/4, 33⅓% = 1/3, 50% = 1/2.",
                           "Increase by x% → multiply by (1 + x/100). Decrease by x% → multiply by (1 − x/100).",
                           "Two changes one after another: multiply the factors (e.g. +20% then −20% → 1.2 × 0.8 = 0.96, a 4% fall)."],
                "traps": ["Dividing by the new value.", "Adding successive percentages (20% + 20% is not 40%)."],
                "scale_up": "Learn the fraction table up to 1/20 and practise 'A is what percent more than B' questions.",
            },
            "U5.7": {
                "zero": "Profit = selling price − cost price. Profit percent is always calculated on the cost price.",
                "method": ["Profit % = profit ÷ CP × 100; Loss % = loss ÷ CP × 100.",
                           "SP = CP × (1 + profit%/100).",
                           "Discount is calculated on the marked price: SP = MP × (1 − discount%/100)."],
                "traps": ["Calculating profit % on the selling price.", "Mixing up the discount base (MP) with the profit base (CP)."],
                "scale_up": "Practise successive discounts and 'false weight' questions.",
            },
            "U5.8": {
                "zero": "Interest is the fee for using money. Simple interest is paid on the original amount only; "
                        "compound interest is also paid on interest already earned.",
                "method": ["Simple interest: SI = P × R × T ÷ 100.",
                           "Compound amount: A = P × (1 + R/100)^T; CI = A − P.",
                           "For 2 years, CI − SI = P × (R/100)²."],
                "traps": ["Forgetting to subtract P to get CI from A.", "Using months where years are needed."],
                "scale_up": "Learn the 'doubling' idea: at simple interest, money doubles when R × T = 100.",
            },
            "U5.9": {
                "zero": "Distance = speed × time. Know any two and you can find the third.",
                "method": ["Convert units: km/h × 5/18 = m/s; m/s × 18/5 = km/h.",
                           "Train passing a pole: distance = length of train. Passing a platform: train + platform.",
                           "Same direction: relative speed = difference. Opposite directions: sum.",
                           "Average speed for equal distances = 2xy ÷ (x + y), not (x + y) ÷ 2."],
                "traps": ["Mixing km/h with metres.", "Averaging speeds directly."],
                "scale_up": "Boats and streams: downstream = boat + stream, upstream = boat − stream.",
            },
            "U5.10": {
                "zero": "If someone finishes a job in 10 days, they do 1/10 of it each day.",
                "method": ["Write each person's one-day work as a fraction.",
                           "Add the fractions for people working together.",
                           "Total days = 1 ÷ (combined one-day work).",
                           "Shortcut: take the LCM of the days as the total work in units."],
                "traps": ["Adding the days instead of the rates."],
                "scale_up": "Pipes and cisterns work the same way; an emptying pipe has negative work.",
            },
            "U5.11": {
                "zero": "Average = total ÷ number of items. Age problems are just equations about people's ages.",
                "method": ["Average: work with totals (total = average × count).",
                           "Ages: let the unknown age be x and write one equation per sentence.",
                           "'n years ago' subtracts n from everyone; 'n years hence' adds n."],
                "traps": ["Changing only one person's age when time passes for both."],
                "scale_up": "Practise 'new person joins / leaves the group' average questions using totals.",
            },
            "U5.12": {
                "zero": "These questions use basic number facts and school algebra: LCM, HCF, divisibility, "
                        "powers, simple equations, and calendar or clock rules.",
                "method": ["LCM = smallest number all divide into; HCF = largest number that divides all.",
                           "For two numbers, LCM × HCF = product of the numbers.",
                           "Divisibility: 3 or 9 → digit sum; 4 → last two digits; 8 → last three digits; 11 → alternating sum.",
                           "Powers: aᵐ × aⁿ = aᵐ⁺ⁿ; aᵐ ÷ aⁿ = aᵐ⁻ⁿ; (aᵐ)ⁿ = aᵐⁿ. Rewrite numbers with the same base first (8 = 2³, 9 = 3²).",
                           "Equations: when stuck, put each option back into the equation; the one that works is the answer."],
                "traps": ["Mixing up LCM and HCF in word problems: 'together again' → LCM; 'largest equal pieces' → HCF."],
                "scale_up": "Learn odd days for calendars and the minute–hour angle formula |30H − 5.5M|.",
            },
        },
    },
    "U6": {
        "overview": "Understanding arguments and categorical propositions, the square of opposition, "
                    "deductive vs inductive reasoning, analogies, Venn diagrams for syllogisms, fallacies, "
                    "uses of language, and Indian logic: pramanas, anumana, vyapti and hetvabhasa.",
        "watch": ["Square of opposition relations", "Syllogism validity by Venn diagram",
                  "Deductive vs inductive", "Formal vs informal fallacies",
                  "Pramanas and which school accepts how many", "Hetvabhasa types"],
        "resources": [
            ("Copi, Cohen & McMahon, Introduction to Logic (book)", None),
            ("IGNOU eGyanKosh: logic and Indian epistemology courses (philosophy)", "https://egyankosh.ac.in"),
            ("NPTEL / SWAYAM courses on logic", "https://nptel.ac.in"),
        ],
        "primers": {
            "U6.1": {
                "zero": "An argument is a set of statements where some (premises) are offered as reasons for "
                        "another (the conclusion). Words like 'therefore', 'hence', 'so' mark a conclusion; "
                        "'because', 'since', 'for' mark a premise.",
                "method": ["Find the conclusion first, then the reasons given for it.",
                           "Deductive: the conclusion is claimed to follow necessarily. It is valid or invalid; "
                           "valid with true premises = sound.",
                           "Inductive: the conclusion is claimed to be probable. It is strong or weak; strong "
                           "with true premises = cogent.",
                           "Valid forms: modus ponens (If P then Q; P; so Q) and modus tollens (If P then Q; not Q; so not P).",
                           "Invalid forms: affirming the consequent (Q; so P) and denying the antecedent (not P; so not Q)."],
                "traps": ["Thinking 'valid' means 'true'. A valid argument can have false premises.",
                          "Calling every generalisation from examples 'deductive'."],
                "scale_up": "Practise identifying the form of arguments with symbols (P, Q) before judging validity.",
            },
            "U6.2": {
                "zero": "A categorical proposition links two classes. There are four kinds: "
                        "A: All S are P · E: No S are P · I: Some S are P · O: Some S are not P.",
                "method": ["Contradictories (A–O, E–I): always opposite. If one is true, the other is false, and vice versa.",
                           "Contraries (A–E): cannot both be true, but can both be false.",
                           "Sub-contraries (I–O): cannot both be false, but can both be true.",
                           "Subalternation (A→I, E→O): if the top is true, the bottom is true; if the bottom is "
                           "false, the top is false. Nothing else follows.",
                           "Distribution: A distributes the subject; E both terms; I neither; O only the predicate."],
                "traps": ["Mixing up contrary and contradictory.",
                          "Inferring 'A is false' from 'I is true' (it does not follow)."],
                "scale_up": "Memorise the square as a picture: A and E on top, I and O below, contradictories on "
                            "the diagonals. Then learn mood and figure (e.g. AAA-1 'Barbara').",
            },
            "U6.3": {
                "zero": "A syllogism has two premises and a conclusion with three terms. A Venn diagram tests it: "
                        "draw one circle per term and shade or mark what the premises say.",
                "method": ["Draw three overlapping circles (S, P, M).",
                           "Draw universal premises (All / No) first: shade the area that must be empty.",
                           "Then draw particular premises (Some): put an X in the area that must have something; "
                           "if the X could fall in two areas, place it on the line.",
                           "Do NOT draw the conclusion. Just read the diagram: is the conclusion already shown?",
                           "Rules check: the middle term must be distributed at least once; two negative premises "
                           "give no conclusion; two particular premises give no conclusion."],
                "traps": ["Drawing the conclusion into the diagram.",
                          "'Some A are B' does not mean 'Some A are not B'."],
                "scale_up": "Practise 'which conclusions definitely follow' with 3–4 statements and 'either–or' cases.",
            },
            "U6.4": {
                "zero": "A fallacy is a mistake in reasoning that can still sound convincing. Formal fallacies "
                        "are errors in the argument's form; informal fallacies are errors in content or language.",
                "method": ["Ask: is the problem the FORM (e.g. affirming the consequent) or the CONTENT?",
                           "Relevance fallacies: ad hominem (attack the person), ad populum (appeal to the crowd), "
                           "ad verecundiam (unjustified authority), ad baculum (threat), ad misericordiam (pity), "
                           "red herring, straw man.",
                           "Presumption: begging the question, complex question, false dichotomy.",
                           "Ambiguity: equivocation (a word shifts meaning), amphiboly (grammar), composition and division.",
                           "Uses of language: informative, expressive, directive. Connotation (intension) = properties; "
                           "denotation (extension) = the things the term applies to."],
                "traps": ["Confusing composition (parts → whole) with division (whole → parts).",
                          "Calling every appeal to an expert a fallacy; only an unjustified one is."],
                "scale_up": "Make a one-line example for each fallacy in your own words.",
            },
            "U6.5": {
                "zero": "An analogy says two things are alike in some ways, so they are probably alike in another.",
                "method": ["State the relationship in the given pair in a full sentence (e.g. 'a pen is used to write').",
                           "Test each option with the same sentence.",
                           "To judge strength: more relevant similarities and fewer relevant differences make it stronger."],
                "traps": ["Accepting a pair that is related but in a different way."],
                "scale_up": "Practise the criteria for appraising analogical arguments.",
            },
            "U6.6": {
                "zero": "A pramana is a valid means of knowledge. Indian schools accept different numbers of them.",
                "method": ["The six: Pratyaksha (perception), Anumana (inference), Upamana (comparison), "
                           "Shabda (verbal testimony), Arthapatti (postulation), Anupalabdhi (non-apprehension).",
                           "Charvaka: 1 (Pratyaksha).",
                           "Buddhism and Vaisheshika: 2 (+ Anumana).",
                           "Samkhya and Yoga: 3 (+ Shabda).",
                           "Nyaya: 4 (+ Upamana).",
                           "Prabhakara Mimamsa: 5 (+ Arthapatti).",
                           "Bhatta Mimamsa and Advaita Vedanta: 6 (+ Anupalabdhi)."],
                "traps": ["Mixing up Upamana (comparison/similarity) and Arthapatti (assuming a fact to explain "
                          "another, e.g. 'fat Devadatta does not eat by day, so he eats at night')."],
                "scale_up": "Learn one standard example for each pramana.",
            },
            "U6.7": {
                "zero": "Anumana (inference) moves from a sign to a conclusion: 'There is fire on the hill, because "
                        "there is smoke.' It depends on vyapti, the invariable link between smoke and fire.",
                "method": ["Terms: Paksha = subject (the hill); Sadhya = what is proved (fire); Hetu = reason (smoke).",
                           "Nyaya's five members: Pratijna (claim), Hetu (reason), Udaharana (example with the "
                           "general rule), Upanaya (application), Nigamana (conclusion).",
                           "Svarthanumana = inference for oneself; Pararthanumana = inference for others (uses five members).",
                           "Hetvabhasa (fallacious reason), five kinds: Savyabhichara (irregular), Viruddha "
                           "(contradictory), Satpratipaksha (counterbalanced), Asiddha (unproved), Badhita "
                           "(contradicted by other evidence)."],
                "traps": ["Mixing up Paksha and Sadhya.", "Mixing up the order of the five members."],
                "scale_up": "Learn the three kinds of inference in early Nyaya: purvavat, sheshavat, samanyatodrishta.",
            },
        },
    },
    "U7": {
        "overview": "Sources and types of data, graphs and charts, interpreting a table or chart (usually a set "
                    "of five questions), and data in governance.",
        "watch": ["Percentage change between years", "Ratios and averages from a table",
                  "Pie chart angles (360° = 100%)", "Types of data (nominal, ordinal, interval, ratio)"],
        "resources": [
            ("NCERT Class 11, Statistics for Economics (free)", "https://ncert.nic.in/textbook.php"),
            ("Open Government Data Platform India", "https://data.gov.in"),
        ],
        "primers": {
            "U7.1": {
                "zero": "Data is either qualitative (categories, words) or quantitative (numbers).",
                "method": ["Nominal: names only (gender, state). Ordinal: ordered (ranks, grades).",
                           "Interval: equal gaps, no true zero (temperature in °C). Ratio: true zero (height, income).",
                           "Primary data: collected by you. Secondary: collected by someone else."],
                "traps": ["Calling ranks 'interval' data."],
                "scale_up": "Match each scale with the statistics allowed (mode / median / mean).",
            },
            "U7.2": {
                "zero": "A chart shows numbers as shapes: bar length, slice size, line height.",
                "method": ["Pie: slice angle = (value ÷ total) × 360°. 1% = 3.6°.",
                           "Histogram: bars touch (continuous classes); bar chart: bars are separate (categories).",
                           "Line graph: best for change over time."],
                "traps": ["Reading a pie angle as a percentage."],
                "scale_up": "Practise converting between angles, percentages and values quickly.",
            },
            "U7.3": {
                "zero": "A DI set gives a table or chart and asks five questions about it. Most need only "
                        "percentages, ratios or averages.",
                "method": ["Read the title, units and column headings before any question.",
                           "For each question, mark the exact cells needed.",
                           "Percentage change = (new − old) ÷ old × 100.",
                           "Estimate with round numbers first; calculate exactly only if two options are close.",
                           "Keep a running total if several questions use the same row or column."],
                "traps": ["Using the wrong year or row.", "Dividing by the new value in percentage change.",
                          "Ignoring units (thousands, lakhs, crores)."],
                "scale_up": "Time yourself: a full DI set in about 6–7 minutes.",
            },
        },
    },
    "U8": {
        "overview": "Computer and internet basics, common abbreviations, e-mail and conferencing, digital "
                    "initiatives in higher education, and ICT in governance.",
        "watch": ["Memory units and number systems (binary, hexadecimal)", "Full forms (URL, HTTP, DNS, IP…)",
                  "E-mail fields (CC, BCC)", "Digital initiatives: SWAYAM, NPTEL, NDLI, e-PG Pathshala, Shodhganga",
                  "Cyber threats (phishing, malware)"],
        "resources": [
            ("NIELIT CCC study material (computer basics)", "https://www.nielit.gov.in"),
            ("Ministry of Education: digital initiatives", "https://www.education.gov.in"),
            ("National Digital Library of India", "https://ndl.iitkgp.ac.in"),
        ],
        "primers": {
            "U8.1": {
                "zero": "Computers store everything as bits (0 or 1). 8 bits = 1 byte.",
                "method": ["Memory units step up by 1024 in binary: KB, MB, GB, TB, PB.",
                           "Binary → decimal: add the place values (…8, 4, 2, 1) where there is a 1. 1011 = 8+2+1 = 11.",
                           "Hexadecimal uses 0–9 and A–F (A=10 … F=15); each hex digit = 4 bits.",
                           "RAM is volatile (lost when power is off); ROM is non-volatile."],
                "traps": ["Mixing bits (b) and bytes (B)."],
                "scale_up": "Practise conversions between binary, octal, decimal and hexadecimal.",
            },
        },
    },
    "U9": {
        "overview": "Development and environment (MDGs, SDGs), human impacts on the environment, pollution and "
                    "health, climate change, energy and natural resources, natural hazards, and Indian and "
                    "international environmental agreements.",
        "watch": ["SDGs (17 goals, 2015–2030)", "Pollutants and their health effects",
                  "Agreements: Montreal (ozone), Kyoto and Paris (climate), CBD, Ramsar", "NAPCC's national missions",
                  "India's renewable energy targets and installed capacity"],
        "resources": [
            ("UN Sustainable Development Goals", "https://sdgs.un.org/goals"),
            ("Ministry of Environment, Forest and Climate Change", "https://moef.gov.in"),
            ("National Disaster Management Authority", "https://ndma.gov.in"),
            ("NCERT Class 11–12 Geography and Biology (environment chapters)", "https://ncert.nic.in/textbook.php"),
        ],
    },
    "U10": {
        "overview": "Higher learning in ancient India, the growth of higher education and research after "
                    "independence, oriental and open/distance programmes, professional and skill-based "
                    "education, value and environmental education, and policies, governance and administration.",
        "watch": ["Ancient universities and where they were", "Commissions (Radhakrishnan 1948–49, Kothari 1964–66)",
                  "NEP 2020 key provisions", "Regulators (UGC, AICTE, NCTE) and NAAC / NIRF",
                  "Constitutional provisions on education"],
        "resources": [
            ("National Education Policy 2020 (full text)", "https://www.education.gov.in"),
            ("University Grants Commission", "https://www.ugc.gov.in"),
            ("NAAC", "https://www.naac.gov.in"),
            ("NIRF rankings", "https://www.nirfindia.org"),
        ],
    },
}

GENERAL_RESOURCES = [
    ("NTA UGC NET site: syllabus, notices, answer keys", "https://ugcnet.nta.ac.in"),
    ("SWAYAM: free courses from Indian universities", "https://swayam.gov.in"),
    ("IGNOU eGyanKosh: free study material", "https://egyankosh.ac.in"),
]


def primer(sid: str):
    uid = sid.split(".")[0]
    return UNIT_GUIDES.get(uid, {}).get("primers", {}).get(sid)
