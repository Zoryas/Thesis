(function(global){
  // Lightweight client-side normalization for assessment objects returned by the API.
  function toStringArray(values){
    if(!Array.isArray(values)) return [];
    return values.map(function(v){ return String(v||"").trim(); });
  }

  function normalizeAssessmentQuestion(question){
    var src = question || {};
    var difficulty = String(src.difficulty || "EASY").trim().toUpperCase();
    var type = String(src.type || "multiple_choice").trim();
    var prompt = String(src.prompt || src.q || "").trim();
    var options = toStringArray(src.options || src.opts || []);
    var answerIndex = Number.isInteger(Number(src.answerIndex)) ? Number(src.answerIndex) : (Number.isInteger(Number(src.ans)) ? Number(src.ans) : 0);
    var answerKey = String(src.answerKey || src.answer || "").trim();
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

  if(typeof global.normalizeAssessmentQuestion !== 'function') global.normalizeAssessmentQuestion = normalizeAssessmentQuestion;
  if(typeof global.normalizeAssessmentData !== 'function') global.normalizeAssessmentData = normalizeAssessmentData;
})(window);
