// ============================================================
// READWISE — All Mock Data (Thesis Prototype)
// ============================================================
const MOCK = {
  students: [
    { id:"s1", name:"Juan Dela Cruz",  grade:"7", section:"Sampaguita", classLevel:"HARD",     preScore:58 },
    { id:"s2", name:"Maria Santos",    grade:"7", section:"Sampaguita", classLevel:"MODERATE", preScore:72 },
    { id:"s3", name:"Carlo Reyes",     grade:"7", section:"Sampaguita", classLevel:"EASY",     preScore:45 }
  ],
  teacher: { name:"Ms. Ana Villanueva", subject:"Grade 7 English", school:"Pulo National High School" },
  passages: [
    { id:"p1", title:"The Water Cycle",                      label:"EASY",     genre:"Expository", words:120, time:2,
      text:`The water cycle is the continuous movement of water through Earth's systems. It begins when the sun heats water in oceans, rivers, and lakes, causing it to evaporate and rise into the atmosphere as water vapor. As this vapor cools at higher altitudes, it condenses around tiny dust particles to form clouds. When enough water droplets gather, they fall back to Earth as precipitation — rain, snow, sleet, or hail. Some water flows across the land as runoff into rivers and back to the ocean. Some soaks into the ground to become groundwater. Plants also return water to the air through a process called transpiration. Together, these processes form the never-ending water cycle that supports all life on our planet.` },
    { id:"p2", title:"The Life of Jose Rizal",               label:"MODERATE", genre:"Narrative",  words:210, time:3,
      text:`José Protasio Rizal Mercado y Alonso Realonda was born on June 19, 1861, in Calamba, Laguna, Philippines. He was the seventh of eleven children of Francisco Rizal Mercado II and Teodora Alonso Realonda. From an early age, he showed remarkable intelligence and a deep love for learning. Rizal was educated at the Ateneo Municipal de Manila, where he excelled in academics and the arts. He later pursued medicine at the University of Santo Tomas and continued his studies in Spain. Abroad, Rizal became acutely aware of the injustices faced by Filipinos under Spanish colonial rule. He channeled his passion into writing, producing his two legendary novels — Noli Me Tangere (1887) and El Filibusterismo (1891) — which stirred the spirit of Filipino nationalism. He also founded La Liga Filipina. His activism led to his arrest and execution by firing squad at Bagumbayan on December 30, 1896. He was only 35 years old. Today, José Rizal is honored as the national hero of the Philippines.` },
    { id:"p3", title:"Climate Change and Its Effects",        label:"HARD",     genre:"Expository", words:310, time:4,
      text:`Climate change refers to long-term shifts in global temperatures and weather patterns. While some climate variation is natural, scientific evidence overwhelmingly shows that human activities — particularly the burning of fossil fuels such as coal, oil, and natural gas — have been the dominant cause since the mid-20th century. These activities release large amounts of carbon dioxide (CO₂) and other greenhouse gases into the atmosphere. The greenhouse effect occurs when these gases trap heat from the sun, preventing it from escaping back into space, causing global warming.\n\nThe consequences are wide-ranging and severe. Rising temperatures cause polar ice caps and glaciers to melt, contributing to sea-level rise that threatens low-lying coastal areas. The Philippines, being an archipelago, is particularly vulnerable to flooding, storm surges, and intensification of typhoons. Warmer ocean temperatures fuel stronger tropical cyclones. Changes in rainfall patterns affect agricultural productivity, leading to food and water insecurity. Coral reefs are bleaching and dying due to ocean acidification.\n\nBiodiversity loss is another critical consequence. Many species cannot adapt quickly enough to changing habitats. Climate change also poses public health risks: the spread of vector-borne diseases like dengue fever is expected to increase as warmer climates expand mosquito habitats. Addressing climate change requires global cooperation, renewable energy transition, forest protection, and sustainable agriculture.` },
    { id:"p4", title:"The Little Prince Summary",            label:"EASY",     genre:"Narrative",  words:140, time:2,
      text:`The Little Prince is a beloved novella by Antoine de Saint-Exupéry, first published in 1943. The story follows a young prince who travels from his tiny home planet to various asteroids and eventually to Earth. On each planet, he meets peculiar grown-ups who represent human flaws — vanity, greed, and blind authority. On Earth, the prince befriends a pilot stranded in the Sahara desert and a wise fox who teaches him: "One sees clearly only with the heart; what is essential is invisible to the eye." The little prince tends to a single rose on his home planet, which he learns to cherish despite her flaws. The story is a gentle reminder that the things that truly matter — love, friendship, and wonder — cannot be seen with the eyes alone.` },
    { id:"p5", title:"Philippine Biodiversity",              label:"MODERATE", genre:"Expository", words:195, time:3,
      text:`The Philippines is one of the world's 17 megadiverse countries, harboring extraordinary variety of plant and animal species. Its unique geographic position in Southeast Asia, combined with thousands of islands and diverse ecosystems — tropical rainforests, mangroves, coral reefs, and mountain ranges — has made it a global hotspot for biodiversity. Scientists estimate the country is home to more than 52,000 species of plants and animals, many of which are endemic — found nowhere else on Earth. The Philippine eagle, the tamaraw, and the tarsier are iconic endemic species. The Tubbataha Reef Natural Park is a UNESCO World Heritage Site and one of the world's finest coral reef ecosystems. Despite this, Philippine biodiversity faces serious threats: deforestation, illegal wildlife trade, coral reef destruction, and climate change. Conservation programs and environmental education in schools play key roles in protecting these natural treasures.` },
    { id:"p6", title:"Constitutional Rights of Citizens",    label:"HARD",     genre:"Expository", words:350, time:5,
      text:`The Constitution of the Philippines, ratified in 1987 following the People Power Revolution, is the supreme law of the land. It establishes the framework of the Philippine government and enumerates fundamental rights every Filipino citizen is entitled to. These rights — the Bill of Rights — are enshrined in Article III and protect individuals from state abuses.\n\nAmong the most fundamental rights is the right to life, liberty, and property. No person shall be deprived of these without due process of law — which has two dimensions: substantive due process (laws must be fair and reasonable) and procedural due process (legal procedures must be just). The equal protection clause mandates no person shall be discriminated against by law.\n\nThe Constitution guarantees freedom of speech, expression, and the press. Citizens may voice opinions, criticize policies, and engage in peaceful assembly. These freedoms are essential to democracy, allowing citizens to hold leaders accountable. However, they are not absolute — they are limited when they infringe on others' rights or pose clear and present danger.\n\nThe right against unreasonable searches and seizures protects citizens' privacy. Law enforcement must obtain a valid warrant before searching or arresting. Evidence gathered illegally is inadmissible under the exclusionary rule. Arrested citizens must be informed of their Miranda rights — the right to remain silent and the right to counsel.\n\nUnderstanding constitutional rights is a civic responsibility. An informed citizenry is the cornerstone of democracy.` }
  ],
  questions: {
    p1:[
      { q:"What process causes water to rise into the atmosphere?",    opts:["Condensation","Evaporation","Precipitation","Transpiration"], ans:1 },
      { q:"What forms when water vapor cools at high altitudes?",       opts:["Rain","Ice","Clouds","Fog"], ans:2 },
      { q:"Which term describes water flowing across land into rivers?",opts:["Transpiration","Evaporation","Groundwater","Runoff"], ans:3 }
    ],
    p2:[
      { q:"Where was Jose Rizal born?",                      opts:["Manila","Batangas","Calamba, Laguna","Cebu"], ans:2 },
      { q:"What was Rizal's first novel?",                   opts:["El Filibusterismo","Noli Me Tangere","Mi Ultimo Adios","La Solidaridad"], ans:1 },
      { q:"What civic organization did Rizal found?",        opts:["Katipunan","La Liga Filipina","Propaganda Movement","Ilustrado Society"], ans:1 }
    ],
    p3:[
      { q:"What is the main cause of climate change?",                  opts:["Volcanic eruptions","Human activities","Ocean currents","Solar flares"], ans:1 },
      { q:"Which gas is primarily responsible for the greenhouse effect?",opts:["Oxygen","Nitrogen","Carbon Dioxide","Hydrogen"], ans:2 },
      { q:"Which is a consequence of climate change mentioned in the passage?",opts:["More snowfall in deserts","Sea-level rise","Decreased typhoons","Lower ocean temperatures"], ans:1 }
    ],
    p4:[
      { q:"Who wrote The Little Prince?",                               opts:["Victor Hugo","Antoine de Saint-Exupéry","Jules Verne","Albert Camus"], ans:1 },
      { q:"What does the fox teach the little prince?",                 opts:["How to survive alone","One sees clearly only with the heart","Money is important","Never trust strangers"], ans:1 },
      { q:"What does the little prince tend to on his home planet?",    opts:["A tree","A garden","A single rose","A fountain"], ans:2 }
    ],
    p5:[
      { q:"How many megadiverse countries are there in the world?",    opts:["10","17","25","30"], ans:1 },
      { q:"Which reef is a UNESCO World Heritage Site?",               opts:["Palawan Reef","Tubbataha Reef Natural Park","Apo Island","Camiguin Reef"], ans:1 },
      { q:"Which is an endemic Philippine species mentioned?",         opts:["Sea turtle","Philippine eagle","Blue whale","Komodo dragon"], ans:1 }
    ],
    p6:[
      { q:"In which article are the Bill of Rights found?",            opts:["Article I","Article II","Article III","Article IV"], ans:2 },
      { q:"What rule makes evidence from illegal searches inadmissible?",opts:["Miranda rule","Exclusionary rule","Due process rule","Equal protection rule"], ans:1 },
      { q:"What are the two dimensions of due process?",               opts:["Civil and criminal","Procedural and substantive","Formal and informal","Written and oral"], ans:1 }
    ]
  },
  shortAnswer: {
    p3:"In your own words, explain one effect of climate change on the Philippines.",
    p6:"Explain what 'due process of law' means in your own words."
  },
  weeklyProgress: {
    s1:[
      { week:1, score:55, difficulty:"HARD",     recommendation:"Maintain" },
      { week:2, score:48, difficulty:"HARD",     recommendation:"Step DOWN to MODERATE" },
      { week:3, score:65, difficulty:"MODERATE", recommendation:"Maintain" },
      { week:4, score:71, difficulty:"MODERATE", recommendation:"Maintain" }
    ],
    s2:[
      { week:1, score:70, difficulty:"MODERATE", recommendation:"Maintain" },
      { week:2, score:75, difficulty:"MODERATE", recommendation:"Step UP to HARD" },
      { week:3, score:68, difficulty:"HARD",     recommendation:"Maintain" },
      { week:4, score:72, difficulty:"HARD",     recommendation:"Maintain" }
    ],
    s3:[
      { week:1, score:42, difficulty:"EASY",     recommendation:"Maintain" },
      { week:2, score:50, difficulty:"EASY",     recommendation:"Maintain" },
      { week:3, score:55, difficulty:"EASY",     recommendation:"Step UP to MODERATE" },
      { week:4, score:48, difficulty:"MODERATE", recommendation:"Step DOWN to EASY" }
    ]
  }
};

const LEGACY_TEXT_PATTERN = /(?:Ã.|Â.|â.|ðŸ|â€|â€™|â€œ|â€\u009d|â€¢|â†|â‰|âœ|â‚)/;

function looksLikeLegacyText(value) {
  return typeof value === "string" && LEGACY_TEXT_PATTERN.test(value);
}

function repairLegacyText(value) {
  let next = String(value || "");
  if (!looksLikeLegacyText(next)) return next;

  for (let attempt = 0; attempt < 3; attempt += 1) {
    if (!looksLikeLegacyText(next)) break;
    try {
      const decoded = decodeURIComponent(escape(next));
      if (!decoded || decoded === next) break;
      next = decoded;
    } catch (error) {
      break;
    }
  }

  return next.replace(/\uFEFF/g, "");
}

function repairLegacyData(value) {
  if (typeof value === "string") return repairLegacyText(value);

  if (Array.isArray(value)) {
    return value.map(function(entry) { return repairLegacyData(entry); });
  }

  if (value && typeof value === "object") {
    Object.keys(value).forEach(function(key) {
      value[key] = repairLegacyData(value[key]);
    });
  }

  return value;
}

repairLegacyData(MOCK);

const PASSAGES_STORAGE_KEY = "readwise_passages_v1";
const ASSIGNMENTS_STORAGE_KEY = "readwise_weekly_assignments_v1";
const ASSIGNMENTS_ACTIVE_WEEK_KEY = "readwise_active_week_v1";
const COMPLETION_STORAGE_KEY = "readwise_weekly_completion_v1";
const THEME_PREFERENCE_KEY = "readwise_theme_preference_v1";
const MAX_WEEKLY_PASSAGES_PER_CLASS = 5;
const TOTAL_PROGRAM_WEEKS = 8;
const CLASS_LEVELS = ["EASY", "MODERATE", "HARD"];
const DEFAULT_PASSAGES = JSON.parse(JSON.stringify(MOCK.passages));
const QUESTION_TYPE_CATALOG = {
  EASY: [
    { value: "multiple_choice", label: "Multiple Choice" },
    { value: "true_false", label: "True or False" }
  ],
  MODERATE: [
    { value: "multiple_choice_harder", label: "Multiple Choice (Harder)" },
    { value: "true_false_modified", label: "True or False (Modified)" },
    { value: "sequence", label: "Sequence" }
  ],
  DIFFICULT: [
    { value: "fill_in_the_blanks", label: "Fill in the Blanks" },
    { value: "identification", label: "Identification" },
    { value: "enumeration", label: "Enumeration" }
  ],
  CUSTOM: [
    { value: "custom", label: "Custom Question" }
  ]
};
const QUESTION_TYPE_LABELS = {};
Object.keys(QUESTION_TYPE_CATALOG).forEach(function(level) {
  QUESTION_TYPE_CATALOG[level].forEach(function(entry) {
    QUESTION_TYPE_LABELS[entry.value] = entry.label;
  });
});

function cloneData(value) {
  return JSON.parse(JSON.stringify(value));
}

function countPassageWords(text) {
  const matches = String(text || "").match(/[A-Za-z]+(?:'[A-Za-z]+)?/g);
  return matches ? matches.length : 0;
}

function estimateReadingTime(wordCount) {
  return Math.max(1, Math.ceil((wordCount || 0) / 80));
}

function normalizeClassLevel(value) {
  const normalized = String(value || "").trim().toUpperCase();
  if (normalized === "DIFFICULT") return "HARD";
  if (CLASS_LEVELS.includes(normalized)) return normalized;
  return "EASY";
}

function getClassDisplayName(level) {
  const normalized = normalizeClassLevel(level);
  return normalized === "HARD" ? "DIFFICULT" : normalized;
}

function mapPassageLabelToClassLevel(label) {
  const normalized = String(label || "").trim().toUpperCase();
  if (normalized === "HARD" || normalized === "DIFFICULT") return "HARD";
  if (normalized === "MODERATE") return "MODERATE";
  return "EASY";
}

function normalizeQuestionDifficulty(value) {
  const normalized = String(value || "").trim().toUpperCase();
  if (QUESTION_TYPE_CATALOG[normalized]) return normalized;
  return "EASY";
}

function mapPassageLabelToQuestionDifficulty(label) {
  const normalized = String(label || "").trim().toUpperCase();
  if (normalized === "HARD") return "DIFFICULT";
  if (normalized === "MODERATE") return "MODERATE";
  return "EASY";
}

function getQuestionTypesForDifficulty(difficulty) {
  const level = normalizeQuestionDifficulty(difficulty);
  return cloneData(QUESTION_TYPE_CATALOG[level]);
}

function getDefaultQuestionType(difficulty) {
  const types = getQuestionTypesForDifficulty(difficulty);
  return types.length ? types[0].value : "multiple_choice";
}

function normalizeQuestionType(type, difficulty) {
  const level = normalizeQuestionDifficulty(difficulty);
  const allowed = QUESTION_TYPE_CATALOG[level].map(function(entry) { return entry.value; });
  const normalized = String(type || "").trim().toLowerCase();
  if (allowed.includes(normalized)) return normalized;
  return allowed[0];
}

function toStringArray(values) {
  if (!Array.isArray(values)) return [];
  return values.map(function(value) { return repairLegacyText(String(value || "").trim()); });
}

function parseDelimitedAnswers(value, delimiter) {
  return String(value || "")
    .split(delimiter)
    .map(function(entry) { return entry.trim(); })
    .filter(function(entry) { return entry; });
}

function normalizeAssessmentQuestion(question) {
  const source = question || {};
  const difficulty = normalizeQuestionDifficulty(
    source.difficulty || source.level || source.category || "EASY"
  );

  let candidateType = String(source.type || "").trim().toLowerCase();
  if (!candidateType) {
    if (Array.isArray(source.opts) || Array.isArray(source.options)) {
      candidateType = difficulty === "MODERATE" ? "multiple_choice_harder" : "multiple_choice";
    } else {
      candidateType = getDefaultQuestionType(difficulty);
    }
  }
  const type = normalizeQuestionType(candidateType, difficulty);

  const prompt = repairLegacyText(String(source.prompt || source.q || "").trim());
  const optionSource = Array.isArray(source.options) ? source.options : source.opts;
  let options = toStringArray(optionSource);
  const answerIndexRaw = source.answerIndex !== undefined ? source.answerIndex : source.ans;
  const answerKeyRaw = source.answerKey !== undefined ? source.answerKey : source.answer;
  const answerKeysRaw = Array.isArray(source.answerKeys) ? source.answerKeys : [];
  const normalized = {
    difficulty: difficulty,
    type: type,
    prompt: prompt,
    options: [],
    answerIndex: 0,
    answerKey: "",
    answerKeys: []
  };

  if (type === "multiple_choice" || type === "multiple_choice_harder") {
    options = options.slice(0, 4);
    while (options.length < 4) options.push("");
    normalized.options = options;

    const parsedIndex = Number(answerIndexRaw);
    normalized.answerIndex = Number.isInteger(parsedIndex) && parsedIndex >= 0 && parsedIndex <= 3
      ? parsedIndex
      : 0;
    return normalized;
  }

  if (type === "true_false" || type === "true_false_modified") {
    const tfAnswer = String(answerKeyRaw || "").trim().toLowerCase();
    normalized.answerKey = tfAnswer === "false" ? "false" : "true";
    return normalized;
  }

  if (type === "sequence") {
    normalized.options = options.filter(function(entry) { return entry; });
    normalized.answerKeys = answerKeysRaw.length
      ? toStringArray(answerKeysRaw).filter(function(entry) { return entry; })
      : parseDelimitedAnswers(answerKeyRaw, ",");
    return normalized;
  }

  if (type === "enumeration") {
    normalized.answerKeys = answerKeysRaw.length
      ? toStringArray(answerKeysRaw).filter(function(entry) { return entry; })
      : parseDelimitedAnswers(answerKeyRaw, ",");
    return normalized;
  }

  normalized.answerKeys = answerKeysRaw.length
    ? toStringArray(answerKeysRaw).filter(function(entry) { return entry; })
    : parseDelimitedAnswers(answerKeyRaw, "|");
  return normalized;
}

function normalizePassageData(passage) {
  const normalized = Object.assign({}, passage);
  normalized.id = normalized.id || "";
  normalized.title = repairLegacyText(String(normalized.title || "").trim());
  normalized.genre = repairLegacyText(String(normalized.genre || "Expository").trim()) || "Expository";
  normalized.text = repairLegacyText(String(normalized.text || "").trim());
  normalized.label = String(normalized.label || "MODERATE").trim().toUpperCase() || "MODERATE";
  normalized.words = countPassageWords(normalized.text);
  normalized.time = estimateReadingTime(normalized.words);

  if (normalized.confidence !== undefined && normalized.confidence !== null && normalized.confidence !== "") {
    normalized.confidence = Number(normalized.confidence);
  } else {
    delete normalized.confidence;
  }

  const legacyQuestions = (MOCK.questions[normalized.id] || []).map(function(question) {
    return {
      difficulty: mapPassageLabelToQuestionDifficulty(normalized.label),
      type: mapPassageLabelToQuestionDifficulty(normalized.label) === "MODERATE"
        ? "multiple_choice_harder"
        : "multiple_choice",
      q: repairLegacyText(String(question.q || "").trim()),
      opts: Array.isArray(question.opts) ? question.opts.slice(0, 4).map(function(opt) { return repairLegacyText(String(opt || "").trim()); }) : ["", "", "", ""],
      ans: Number.isInteger(question.ans) ? question.ans : 0
    };
  });
  const legacyShortAnswer = repairLegacyText(String(MOCK.shortAnswer[normalized.id] || "").trim());
  normalized.assessment = normalizeAssessmentData(normalized.assessment || {
    questions: legacyQuestions,
    shortAnswerPrompt: legacyShortAnswer
  });

  return normalized;
}

function normalizeAssessmentData(assessment) {
  const source = assessment || {};
  const normalizedQuestions = Array.isArray(source.questions) ? source.questions : [];
  const questions = normalizedQuestions
    .map(function(question) { return normalizeAssessmentQuestion(question); })
    .filter(function(question) { return question.prompt; });

  return {
    questions: questions,
    shortAnswerPrompt: repairLegacyText(String(source.shortAnswerPrompt || source.shortAnswer || "").trim())
  };
}

function loadStoredPassages() {
  try {
    const raw = localStorage.getItem(PASSAGES_STORAGE_KEY);
    if (!raw) return DEFAULT_PASSAGES.map(normalizePassageData);

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return DEFAULT_PASSAGES.map(normalizePassageData);
    return parsed.map(normalizePassageData);
  } catch (error) {
    return DEFAULT_PASSAGES.map(normalizePassageData);
  }
}

function normalizeWeekNumber(week) {
  const parsed = Number(week);
  if (!Number.isInteger(parsed) || parsed < 1) return 1;
  if (parsed > TOTAL_PROGRAM_WEEKS) return TOTAL_PROGRAM_WEEKS;
  return parsed;
}

function createEmptyWeekAssignment() {
  return {
    EASY: [],
    MODERATE: [],
    HARD: []
  };
}

function createDefaultAssignmentsTemplate() {
  const assignments = {};
  for (let week = 1; week <= TOTAL_PROGRAM_WEEKS; week++) {
    assignments[String(week)] = createEmptyWeekAssignment();
  }
  return assignments;
}

function createAutoFilledAssignmentsTemplate() {
  const assignments = createDefaultAssignmentsTemplate();
  Object.keys(assignments).forEach(function(weekKey) {
    CLASS_LEVELS.forEach(function(level) {
      fillWeekClassToLimit(assignments[weekKey], level);
    });
  });
  return assignments;
}

function getPassagesByClassLevel(classLevel) {
  const normalized = normalizeClassLevel(classLevel);
  return MOCK.passages.filter(function(passage) {
    return mapPassageLabelToClassLevel(passage.label) === normalized;
  });
}

function dedupeIds(ids) {
  const seen = new Set();
  const output = [];
  ids.forEach(function(id) {
    const clean = String(id || "").trim();
    if (!clean || seen.has(clean)) return;
    seen.add(clean);
    output.push(clean);
  });
  return output;
}

function fillWeekClassToLimit(weekAssignments, classLevel) {
  const level = normalizeClassLevel(classLevel);
  const current = Array.isArray(weekAssignments[level]) ? weekAssignments[level].slice() : [];
  const pool = getPassagesByClassLevel(level).map(function(passage) { return passage.id; });
  const filled = dedupeIds(current).filter(function(id) { return pool.includes(id); });

  let pointer = 0;
  while (filled.length < MAX_WEEKLY_PASSAGES_PER_CLASS && pool.length > 0 && pointer < pool.length * 3) {
    const candidate = pool[pointer % pool.length];
    if (!filled.includes(candidate)) filled.push(candidate);
    pointer++;
    if (filled.length >= pool.length) break;
  }

  weekAssignments[level] = filled.slice(0, MAX_WEEKLY_PASSAGES_PER_CLASS);
}

function normalizeAssignments(assignments) {
  const source = assignments || {};
  const normalized = createDefaultAssignmentsTemplate();

  Object.keys(normalized).forEach(function(weekKey) {
    const weekSource = source[weekKey] || {};
    CLASS_LEVELS.forEach(function(level) {
      const ids = Array.isArray(weekSource[level]) ? weekSource[level].slice() : [];
      const matching = getPassagesByClassLevel(level).map(function(passage) { return passage.id; });
      normalized[weekKey][level] = dedupeIds(ids).filter(function(id) { return matching.includes(id); }).slice(0, MAX_WEEKLY_PASSAGES_PER_CLASS);
    });
  });

  return normalized;
}

function loadStoredAssignments() {
  try {
    const raw = localStorage.getItem(ASSIGNMENTS_STORAGE_KEY);
    if (!raw) return normalizeAssignments(createAutoFilledAssignmentsTemplate());
    const parsed = JSON.parse(raw);
    return normalizeAssignments(parsed);
  } catch (error) {
    return normalizeAssignments(createAutoFilledAssignmentsTemplate());
  }
}

function saveAssignments(assignments) {
  const normalized = normalizeAssignments(assignments);
  try {
    localStorage.setItem(ASSIGNMENTS_STORAGE_KEY, JSON.stringify(normalized));
  } catch (error) {
    console.warn("Unable to save assignments:", error);
  }
  return normalized;
}

function getActiveWeek() {
  const stored = localStorage.getItem(ASSIGNMENTS_ACTIVE_WEEK_KEY);
  return normalizeWeekNumber(stored || 1);
}

function setActiveWeek(week) {
  const normalized = normalizeWeekNumber(week);
  try {
    localStorage.setItem(ASSIGNMENTS_ACTIVE_WEEK_KEY, String(normalized));
  } catch (error) {
    console.warn("Unable to persist active week:", error);
  }
  return normalized;
}

function getWeeklyAssignments(week) {
  const normalizedWeek = normalizeWeekNumber(week);
  const assignments = loadStoredAssignments();
  return cloneData(assignments[String(normalizedWeek)] || createEmptyWeekAssignment());
}

function setWeeklyAssignments(week, weeklyData) {
  const normalizedWeek = normalizeWeekNumber(week);
  const assignments = loadStoredAssignments();
  assignments[String(normalizedWeek)] = Object.assign(createEmptyWeekAssignment(), weeklyData || {});
  return saveAssignments(assignments);
}

function isPassageAssignableToClass(passageId, classLevel) {
  const passage = getPassage(passageId);
  if (!passage) return false;
  return mapPassageLabelToClassLevel(passage.label) === normalizeClassLevel(classLevel);
}

function assignPassageToWeekClass(week, classLevel, passageId) {
  const weekNumber = normalizeWeekNumber(week);
  const level = normalizeClassLevel(classLevel);
  const passage = getPassage(passageId);
  if (!passage) return { ok: false, message: "Passage not found." };
  if (!isPassageAssignableToClass(passageId, level)) {
    return { ok: false, message: "Passage label does not match class level." };
  }

  const assignments = loadStoredAssignments();
  const weekKey = String(weekNumber);
  const list = assignments[weekKey][level] || [];
  if (list.includes(passageId)) return { ok: true, message: "Passage already assigned." };
  if (list.length >= MAX_WEEKLY_PASSAGES_PER_CLASS) {
    return { ok: false, message: "Class already has 5 passages this week." };
  }

  list.push(passageId);
  assignments[weekKey][level] = dedupeIds(list).slice(0, MAX_WEEKLY_PASSAGES_PER_CLASS);
  saveAssignments(assignments);
  return { ok: true, message: "Passage assigned." };
}

function removePassageFromWeekClass(week, classLevel, passageId) {
  const weekNumber = normalizeWeekNumber(week);
  const level = normalizeClassLevel(classLevel);
  const assignments = loadStoredAssignments();
  const weekKey = String(weekNumber);
  const list = Array.isArray(assignments[weekKey][level]) ? assignments[weekKey][level] : [];
  assignments[weekKey][level] = list.filter(function(id) { return id !== passageId; });
  saveAssignments(assignments);
  return true;
}

function autofillWeekClass(week, classLevel) {
  const weekNumber = normalizeWeekNumber(week);
  const level = normalizeClassLevel(classLevel);
  const assignments = loadStoredAssignments();
  const weekKey = String(weekNumber);
  fillWeekClassToLimit(assignments[weekKey], level);
  saveAssignments(assignments);
  return cloneData(assignments[weekKey][level]);
}

function loadCompletionData() {
  try {
    const raw = localStorage.getItem(COMPLETION_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (error) {
    return {};
  }
}

function saveCompletionData(data) {
  try {
    localStorage.setItem(COMPLETION_STORAGE_KEY, JSON.stringify(data || {}));
  } catch (error) {
    console.warn("Unable to save completion data:", error);
  }
}

function getCompletionKey(studentId, week) {
  return String(studentId || "") + "::week" + normalizeWeekNumber(week);
}

function markPassageCompleted(studentId, week, passageId) {
  const key = getCompletionKey(studentId, week);
  const data = loadCompletionData();
  const current = Array.isArray(data[key]) ? data[key] : [];
  if (!current.includes(passageId)) current.push(passageId);
  data[key] = current;
  saveCompletionData(data);
  return cloneData(current);
}

function getCompletedPassages(studentId, week) {
  const key = getCompletionKey(studentId, week);
  const data = loadCompletionData();
  return Array.isArray(data[key]) ? cloneData(data[key]) : [];
}

function isPassageCompleted(studentId, week, passageId) {
  return getCompletedPassages(studentId, week).includes(passageId);
}

function getStudentWeeklyPassages(studentOrId, week) {
  const student = typeof studentOrId === "string" ? getStudent(studentOrId) : studentOrId;
  if (!student) return [];
  const classLevel = normalizeClassLevel(student.classLevel);
  const weekAssignments = getWeeklyAssignments(week);
  const ids = Array.isArray(weekAssignments[classLevel]) ? weekAssignments[classLevel] : [];
  return ids.map(function(id) { return getPassage(id); }).filter(Boolean);
}

function commitPassages(passages) {
  const normalized = passages.map(normalizePassageData);
  MOCK.passages = normalized;

  try {
    localStorage.setItem(PASSAGES_STORAGE_KEY, JSON.stringify(normalized));
  } catch (error) {
    console.warn("Unable to persist passages:", error);
  }

  return normalized;
}

function getNextPassageId(passages) {
  let maxId = 0;
  passages.forEach(function(passage) {
    const match = /^p(\d+)$/.exec(String(passage.id || ""));
    if (match) maxId = Math.max(maxId, Number(match[1]));
  });
  return "p" + (maxId + 1);
}

MOCK.passages = loadStoredPassages();

// Helpers
function getStudent(id)       { return MOCK.students.find(s=>s.id===id); }
function getPassage(id)       { return MOCK.passages.find(p=>p.id===id); }
function getPassages()        { return cloneData(MOCK.passages); }
function getCurrentStudent()  { return getStudent(sessionStorage.getItem("studentId")||"s1"); }
function themeColor(name, fallback) {
  if (typeof window === "undefined" || !window.getComputedStyle || !document.documentElement) {
    return fallback;
  }
  const value = window.getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}
function isDarkAppearance()   {
  return typeof document !== "undefined" &&
    document.documentElement &&
    document.documentElement.dataset.appearance === "dark";
}
function levelColor(l) {
  const level = normalizeClassLevel(l);
  if (level === "EASY") return themeColor("--easy", "#34c759");
  if (level === "MODERATE") return themeColor("--moderate", "#ff9f0a");
  return themeColor("--hard", "#ff453a");
}
function levelBg(l) {
  const level = normalizeClassLevel(l);
  const alpha = isDarkAppearance() ? 0.22 : 0.14;
  if (level === "EASY") return "rgba(52, 199, 89, " + alpha + ")";
  if (level === "MODERATE") return "rgba(255, 159, 10, " + alpha + ")";
  return "rgba(255, 69, 58, " + alpha + ")";
}
function badgeClass(l)        { return l==="EASY"?"badge-easy":l==="MODERATE"?"badge-moderate":"badge-hard"; }
function getAssignedPassage(s) {
  const week = getActiveWeek();
  const weekly = getStudentWeeklyPassages(s, week);
  if (!weekly.length) return MOCK.passages.find(function(p){ return p.label===s.classLevel; }) || null;

  const completed = getCompletedPassages(s.id, week);
  const next = weekly.find(function(passage) { return !completed.includes(passage.id); });
  return next || weekly[0];
}
function savePassage(data) {
  const passages = getPassages();
  const isEdit = Boolean(data && data.id);
  const nextId = isEdit ? data.id : getNextPassageId(passages);
  const record = normalizePassageData(Object.assign({}, data, {
    id: nextId,
    assessment: normalizeAssessmentData(data ? data.assessment : null)
  }));
  const index = passages.findIndex(function(passage) { return passage.id === nextId; });

  if (index >= 0) passages[index] = record;
  else passages.unshift(record);

  commitPassages(passages);
  return cloneData(record);
}
function deletePassage(id) {
  const passages = getPassages();
  const filtered = passages.filter(function(passage) { return passage.id !== id; });
  if (filtered.length === passages.length) return false;
  commitPassages(filtered);
  return true;
}
function getPassageAssessment(id) {
  const passage = getPassage(id);
  if (!passage) return { questions: [], shortAnswerPrompt: "" };

  if (passage.assessment) return cloneData(normalizeAssessmentData(passage.assessment));

  return normalizeAssessmentData({
    questions: MOCK.questions[id] || [],
    shortAnswerPrompt: MOCK.shortAnswer[id] || ""
  });
}
function getQuestionTypeCatalog() {
  return cloneData(QUESTION_TYPE_CATALOG);
}
function getQuestionTypeLabel(type) {
  return QUESTION_TYPE_LABELS[String(type || "").trim().toLowerCase()] || "Question";
}
function showToast(msg,color="#2c3e6b") {
  const t=document.getElementById("toast");
  if(!t)return;
  t.textContent=repairLegacyText(msg); t.style.background=color; t.style.display="block";
  setTimeout(()=>t.style.display="none",2800);
}

function repairLegacyDom(root) {
  if (!root || !root.querySelectorAll) return;

  document.title = repairLegacyText(document.title);

  const textWalker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: function(node) {
      if (!node.parentElement) return NodeFilter.FILTER_REJECT;
      const tag = node.parentElement.tagName;
      if (tag === "SCRIPT" || tag === "STYLE") return NodeFilter.FILTER_REJECT;
      return looksLikeLegacyText(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    }
  });

  const textNodes = [];
  while (textWalker.nextNode()) textNodes.push(textWalker.currentNode);
  textNodes.forEach(function(node) {
    node.nodeValue = repairLegacyText(node.nodeValue);
  });

  root.querySelectorAll("[title],[placeholder],[aria-label]").forEach(function(element) {
    if (element.hasAttribute("title")) {
      element.setAttribute("title", repairLegacyText(element.getAttribute("title")));
    }
    if (element.hasAttribute("placeholder")) {
      element.setAttribute("placeholder", repairLegacyText(element.getAttribute("placeholder")));
    }
    if (element.hasAttribute("aria-label")) {
      element.setAttribute("aria-label", repairLegacyText(element.getAttribute("aria-label")));
    }
  });
}

function initLegacyDomRepair() {
  if (window.__READWISE_TEXT_REPAIR_READY) return;
  window.__READWISE_TEXT_REPAIR_READY = true;

  repairLegacyDom(document.body);

  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === "characterData" && looksLikeLegacyText(mutation.target.nodeValue)) {
        mutation.target.nodeValue = repairLegacyText(mutation.target.nodeValue);
        return;
      }

      if (mutation.type === "attributes" && mutation.target) {
        const attr = mutation.attributeName;
        const current = mutation.target.getAttribute(attr);
        if (current && looksLikeLegacyText(current)) {
          mutation.target.setAttribute(attr, repairLegacyText(current));
        }
        return;
      }

      mutation.addedNodes.forEach(function(node) {
        if (node.nodeType === Node.TEXT_NODE && looksLikeLegacyText(node.nodeValue)) {
          node.nodeValue = repairLegacyText(node.nodeValue);
          return;
        }

        if (node.nodeType === Node.ELEMENT_NODE) {
          repairLegacyDom(node);
        }
      });
    });
  });

  observer.observe(document.body, {
    subtree: true,
    childList: true,
    characterData: true,
    attributes: true,
    attributeFilter: ["title", "placeholder", "aria-label"]
  });
}

const SHELL_NAV_ITEMS = {
  "teacher-dashboard.html": { label: "Dashboard", icon: "home" },
  "teacher-passages.html": { label: "Passage Library", icon: "books" },
  "teacher-submit.html": { label: "Submit Passage", icon: "plus-square" },
  "teacher-students.html": { label: "Students", icon: "users" },
  "teacher-recommendations.html": { label: "Recommendations", icon: "bell" },
  "teacher-reports.html": { label: "Reports", icon: "chart" },
  "student-profile.html": { label: "My Profile", icon: "person" },
  "student-dashboard.html": { label: "Dashboard", icon: "home" },
  "student-passage.html": { label: "My Passage", icon: "book" },
  "student-progress.html": { label: "My Progress", icon: "chart" },
  "student-pre-assessment.html": { label: "Pre-Assessment", icon: "checklist" }
};

const SHELL_ICON_PATHS = {
  menu: '<path d="M5 7.5h14"></path><path d="M5 12h14"></path><path d="M5 16.5h14"></path>',
  close: '<path d="M7 7l10 10"></path><path d="M17 7L7 17"></path>',
  sidebar: '<rect x="4.5" y="5" width="15" height="14" rx="2.5"></rect><path d="M10 5v14"></path>',
  sun: '<circle cx="12" cy="12" r="3.5"></circle><path d="M12 3.5v2"></path><path d="M12 18.5v2"></path><path d="M20.5 12h-2"></path><path d="M5.5 12h-2"></path><path d="M17.7 6.3 16.3 7.7"></path><path d="M7.7 16.3 6.3 17.7"></path><path d="M17.7 17.7 16.3 16.3"></path><path d="M7.7 7.7 6.3 6.3"></path>',
  moon: '<path d="M18.2 14.6A6.8 6.8 0 0 1 9.4 5.8a7.6 7.6 0 1 0 8.8 8.8Z"></path>',
  home: '<path d="M4.5 10.5L12 4l7.5 6.5"></path><path d="M7.5 10.5V19h9v-8.5"></path>',
  books: '<path d="M6 5.5h10.5A1.5 1.5 0 0 1 18 7v12H7.5A2.5 2.5 0 0 0 5 21.5V7A1.5 1.5 0 0 1 6.5 5.5Z"></path><path d="M5 18.5A2.5 2.5 0 0 1 7.5 16H18"></path>',
  "plus-square": '<rect x="5" y="5" width="14" height="14" rx="3"></rect><path d="M12 8.5v7"></path><path d="M8.5 12h7"></path>',
  users: '<path d="M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"></path><path d="M15.5 12.5a2.5 2.5 0 1 0 0-5"></path><path d="M4.5 18.5c1.1-2.1 3-3 5-3s3.9.9 5 3"></path><path d="M14.5 15.8c1.3.2 2.5 1 3.3 2.4"></path>',
  bell: '<path d="M8 18.5h8"></path><path d="M9.5 18.5a2.5 2.5 0 0 0 5 0"></path><path d="M6.5 15.5h11l-1.4-2.4v-2.4a4.1 4.1 0 1 0-8.2 0v2.4Z"></path>',
  chart: '<path d="M5 19V9.5"></path><path d="M12 19V5"></path><path d="M19 19v-7"></path><path d="M4 19h16"></path>',
  person: '<path d="M12 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"></path><path d="M5 19c1.2-2.7 3.8-4.2 7-4.2s5.8 1.5 7 4.2"></path>',
  book: '<path d="M7 5.5h10.5A1.5 1.5 0 0 1 19 7v11.5H8A3 3 0 0 0 5 21.5V7.5A2 2 0 0 1 7 5.5Z"></path><path d="M8 9h7"></path><path d="M8 12h7"></path>',
  checklist: '<rect x="5" y="4.5" width="14" height="15" rx="3"></rect><path d="M9 8.5h6"></path><path d="M9 12h6"></path><path d="M9 15.5h4"></path><path d="M7.2 8.5h.1"></path><path d="M7.2 12h.1"></path><path d="M7.2 15.5h.1"></path>',
  logout: '<path d="M10 7.5V6a2 2 0 0 1 2-2h5v16h-5a2 2 0 0 1-2-2v-1.5"></path><path d="M13 12H5.5"></path><path d="M8.5 8.5L5 12l3.5 3.5"></path>'
};

function getShellPageName(href) {
  const value = String(href || "").split("#")[0].split("?")[0];
  return value.slice(value.lastIndexOf("/") + 1);
}

function getShellIcon(name) {
  const paths = SHELL_ICON_PATHS[name] || SHELL_ICON_PATHS.home;
  return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + paths + "</svg>";
}

function getStoredThemePreference() {
  try {
    const value = localStorage.getItem(THEME_PREFERENCE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch (error) {
    return null;
  }
}

function storeThemePreference(value) {
  try {
    if (value === "light" || value === "dark") {
      localStorage.setItem(THEME_PREFERENCE_KEY, value);
    } else {
      localStorage.removeItem(THEME_PREFERENCE_KEY);
    }
  } catch (error) {
    console.warn("Unable to persist theme preference:", error);
  }
}

function applyChartTheme() {
  if (!window.Chart) return;
  const styles = getComputedStyle(document.documentElement);
  const labelColor = styles.getPropertyValue("--text-soft").trim() || "#6e6e73";
  const gridColor = styles.getPropertyValue("--chart-grid").trim() || "rgba(60, 60, 67, 0.16)";
  Chart.defaults.color = labelColor;
  Chart.defaults.borderColor = gridColor;

  const chartInstances = window.Chart.instances || {};
  Object.keys(chartInstances).forEach(function(key) {
    const chart = chartInstances[key];
    if (!chart || !chart.options) return;
    chart.options.color = labelColor;
    if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
      chart.options.plugins.legend.labels.color = labelColor;
    }
    if (chart.options.scales) {
      Object.keys(chart.options.scales).forEach(function(scaleKey) {
        const scale = chart.options.scales[scaleKey];
        if (!scale) return;
        scale.grid = Object.assign({}, scale.grid, { color: gridColor });
        scale.ticks = Object.assign({}, scale.ticks, { color: labelColor });
      });
    }
    chart.update("none");
  });
}

function initReadWiseThemeSync() {
  if (typeof window === "undefined" || !window.matchMedia || !document.documentElement) return;
  if (window.__READWISE_THEME_SYNC_READY) return;
  window.__READWISE_THEME_SYNC_READY = true;

  const colorQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const contrastQuery = window.matchMedia("(prefers-contrast: more)");

  function syncThemeState() {
    const preference = getStoredThemePreference();
    const appearance = preference || (colorQuery.matches ? "dark" : "light");
    document.documentElement.style.colorScheme = appearance;
    document.documentElement.dataset.appearance = appearance;
    document.documentElement.dataset.themePreference = preference || "system";
    document.documentElement.dataset.contrast = contrastQuery.matches ? "more" : "standard";
    applyChartTheme();
    window.dispatchEvent(new CustomEvent("readwise:themechange", {
      detail: {
        appearance: appearance,
        preference: preference || "system",
        contrast: document.documentElement.dataset.contrast
      }
    }));
  }

  if (typeof colorQuery.addEventListener === "function") {
    colorQuery.addEventListener("change", syncThemeState);
    contrastQuery.addEventListener("change", syncThemeState);
  } else if (typeof colorQuery.addListener === "function") {
    colorQuery.addListener(syncThemeState);
    contrastQuery.addListener(syncThemeState);
  }

  window.getReadWiseThemePreference = function() {
    return getStoredThemePreference() || document.documentElement.dataset.appearance || (colorQuery.matches ? "dark" : "light");
  };

  window.setReadWiseThemePreference = function(value) {
    storeThemePreference(value);
    syncThemeState();
  };

  window.clearReadWiseThemePreference = function() {
    storeThemePreference(null);
    syncThemeState();
  };

  window.addEventListener("storage", function(event) {
    if (event.key === THEME_PREFERENCE_KEY) syncThemeState();
  });

  syncThemeState();
}

function initReadWiseShell() {
  if (window.__READWISE_SHELL_READY) return;
  window.__READWISE_SHELL_READY = true;

  const body = document.body;
  const layout = document.querySelector(".layout");
  const sidebar = document.querySelector(".sidebar");
  if (!body || !layout || !sidebar) return;

  const banner = document.querySelector(".demo-banner");
  if (banner) banner.textContent = "ReadWise System | Pulo National High School";

  if (!sidebar.id) sidebar.id = "app-sidebar";

  const navLinks = Array.from(sidebar.querySelectorAll("nav a"));
  navLinks.forEach(function(link) {
    const pageName = getShellPageName(link.getAttribute("href"));
    const meta = SHELL_NAV_ITEMS[pageName];
    if (!meta) return;
    link.innerHTML =
      '<span class="icon" aria-hidden="true">' + getShellIcon(meta.icon) + '</span>' +
      '<span class="nav-label">' + meta.label + "</span>";
    link.setAttribute("title", meta.label);
  });

  const logoutButton = sidebar.querySelector(".logout-btn");
  if (logoutButton) {
    logoutButton.innerHTML =
      '<span class="icon" aria-hidden="true">' + getShellIcon("logout") + '</span>' +
      '<span class="nav-label">Logout</span>';
    logoutButton.setAttribute("type", "button");
  }

  let themeSwitch = sidebar.querySelector(".theme-switch");
  if (!themeSwitch) {
    themeSwitch = document.createElement("div");
    themeSwitch.className = "theme-switch";
    themeSwitch.innerHTML =
      '<div class="theme-switch-label">Appearance</div>' +
      '<div class="theme-switch-segment" role="group" aria-label="Appearance">' +
        '<button class="theme-option" type="button" data-theme-value="light">' +
          '<span class="icon" aria-hidden="true">' + getShellIcon("sun") + '</span>' +
          '<span class="theme-option-label">Light</span>' +
        "</button>" +
        '<button class="theme-option" type="button" data-theme-value="dark">' +
          '<span class="icon" aria-hidden="true">' + getShellIcon("moon") + '</span>' +
          '<span class="theme-option-label">Dark</span>' +
        "</button>" +
      "</div>";

    const footer = sidebar.querySelector(".sidebar-footer");
    if (footer) {
      if (logoutButton) footer.insertBefore(themeSwitch, logoutButton);
      else footer.appendChild(themeSwitch);
    }
  }

  const themeButtons = Array.from(sidebar.querySelectorAll(".theme-option"));

  function syncThemeButtons() {
    const activeTheme = document.documentElement.dataset.appearance || "light";
    themeButtons.forEach(function(button) {
      const isActive = button.dataset.themeValue === activeTheme;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  themeButtons.forEach(function(button) {
    button.addEventListener("click", function() {
      if (typeof window.setReadWiseThemePreference === "function") {
        window.setReadWiseThemePreference(button.dataset.themeValue);
      }
    });
  });

  window.addEventListener("readwise:themechange", syncThemeButtons);
  syncThemeButtons();

  let overlay = document.querySelector(".sidebar-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "sidebar-overlay";
    body.insertBefore(overlay, layout);
  }

  let toggle = document.querySelector(".shell-toggle");
  if (!toggle) {
    toggle = document.createElement("button");
    toggle.className = "shell-toggle";
    toggle.type = "button";
    toggle.setAttribute("aria-controls", sidebar.id);
    toggle.innerHTML = '<span class="icon" aria-hidden="true">' + getShellIcon("sidebar") + "</span>";
    body.insertBefore(toggle, layout);
  }

  const collapseKey = "readwise.sidebar.collapsed";
  const mobileQuery = window.matchMedia("(max-width: 900px)");

  function updateTogglePresentation() {
    const isMobile = mobileQuery.matches;
    const isOpen = isMobile ? body.classList.contains("sidebar-open") : !body.classList.contains("sidebar-collapsed");
    const iconName = isMobile ? (isOpen ? "close" : "sidebar") : "sidebar";
    toggle.innerHTML = '<span class="icon" aria-hidden="true">' + getShellIcon(iconName) + "</span>";
  }

  function syncShellState() {
    const isMobile = mobileQuery.matches;
    body.classList.toggle("sidebar-mobile", isMobile);
    if (isMobile) {
      body.classList.remove("sidebar-collapsed");
      body.classList.remove("sidebar-open");
    } else {
      body.classList.remove("sidebar-open");
      const collapsed = sessionStorage.getItem(collapseKey) === "1";
      body.classList.toggle("sidebar-collapsed", collapsed);
    }
    updateToggleA11y();
    updateTogglePresentation();
  }

  function updateToggleA11y() {
    const isMobile = mobileQuery.matches;
    const expanded = isMobile ? body.classList.contains("sidebar-open") : !body.classList.contains("sidebar-collapsed");
    toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    toggle.setAttribute("aria-label", expanded ? "Close navigation" : "Open navigation");
  }

  function closeMobileSidebar() {
    if (!mobileQuery.matches) return;
    body.classList.remove("sidebar-open");
    updateToggleA11y();
    updateTogglePresentation();
  }

  toggle.addEventListener("click", function() {
    if (mobileQuery.matches) {
      body.classList.toggle("sidebar-open");
    } else {
      const nextCollapsed = !body.classList.contains("sidebar-collapsed");
      body.classList.toggle("sidebar-collapsed", nextCollapsed);
      sessionStorage.setItem(collapseKey, nextCollapsed ? "1" : "0");
    }
    updateToggleA11y();
    updateTogglePresentation();
  });

  overlay.addEventListener("click", closeMobileSidebar);

  navLinks.forEach(function(link) {
    link.addEventListener("click", closeMobileSidebar);
  });

  document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") closeMobileSidebar();
  });

  if (typeof mobileQuery.addEventListener === "function") {
    mobileQuery.addEventListener("change", syncShellState);
  } else if (typeof mobileQuery.addListener === "function") {
    mobileQuery.addListener(syncShellState);
  }

  syncShellState();
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
  initReadWiseThemeSync();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function() {
      initLegacyDomRepair();
      initReadWiseShell();
    });
  } else {
    initLegacyDomRepair();
    initReadWiseShell();
  }
}
