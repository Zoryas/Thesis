(function(global){
  // Lightweight client-side normalization for assessment objects returned by the API.
  function toStringArray(values){
    if (Array.isArray(values)) {
      return values.map(function(v){ return String(v||"").trim(); });
    }
    if (typeof values === "string") {
      return values.split(/\s*[|,]\s*/).map(function(v){ return String(v||"").trim(); }).filter(Boolean);
    }
    return [];
  }

  function normalizeQuestionDifficulty(level){
    var raw = String(level || "").trim().toUpperCase();
    if (raw === "HARD" || raw === "DIFFICULT") return "DIFFICULT";
    if (raw === "MODERATE" || raw === "MEDIUM") return "MODERATE";
    return "EASY";
  }

  function normalizeQuestionType(type){
    var raw = String(type || "").trim().toLowerCase();
    if (raw === "fill_blank") return "fill_in_the_blanks";
    return raw;
  }

  function mapPassageLabelToQuestionDifficulty(label){
    return normalizeQuestionDifficulty(label);
  }

  function normalizeAssessmentQuestion(question){
    var src = question || {};
    var difficulty = normalizeQuestionDifficulty(src.difficulty || "EASY");
    var type = normalizeQuestionType(src.type || "multiple_choice");
    var prompt = String(src.prompt || src.q || "").trim();
    var options = toStringArray(src.options || src.opts || []);
    var answerIndex = Number.isInteger(Number(src.answerIndex)) ? Number(src.answerIndex) : (Number.isInteger(Number(src.ans)) ? Number(src.ans) : 0);
    var answerKey = String(src.answerKey || src.answer || "").trim().toLowerCase();
    var answerKeys = Array.isArray(src.answerKeys) ? toStringArray(src.answerKeys) : toStringArray(src.answerKeys || src.answer || "").filter(Boolean);

    return {
      difficulty: difficulty,
      type: type,
      prompt: prompt,
      options: options,
      answerIndex: answerIndex,
      answerKey: answerKey,
      answerKeys: answerKeys
    };
  }

  function normalizeAssessmentData(assessment){
    var src = assessment || {};
    var qs = Array.isArray(src.questions) ? src.questions.map(normalizeAssessmentQuestion) : [];
    qs = qs.filter(function(q){ return q && String(q.prompt||"").trim(); });
    return { questions: qs, shortAnswerPrompt: String(src.shortAnswerPrompt || src.shortAnswer || "").trim() };
  }

  if(typeof global.normalizeQuestionDifficulty !== 'function') global.normalizeQuestionDifficulty = normalizeQuestionDifficulty;
  if(typeof global.mapPassageLabelToQuestionDifficulty !== 'function') global.mapPassageLabelToQuestionDifficulty = mapPassageLabelToQuestionDifficulty;
  if(typeof global.normalizeAssessmentQuestion !== 'function') global.normalizeAssessmentQuestion = normalizeAssessmentQuestion;
  if(typeof global.normalizeAssessmentData !== 'function') global.normalizeAssessmentData = normalizeAssessmentData;
})(window);
