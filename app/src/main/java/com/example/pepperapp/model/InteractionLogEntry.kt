package com.example.pepperapp.model

data class InteractionLogEntry(
    val timestamp: Long,
    val sessionId: String,
    val turnIndex: Int,
    val userRawSpeech: String?,
    val asrTranscript: String,
    val languageDetected: String,
    val phqQuestionId: String?,
    val handlingModule: String,      // "PEPPER_LOCAL" or "GPT_FALLBACK"
    val pepperLocalNlpSuccess: Boolean,
    val gptUsed: Boolean,
    val gptReason: String?,
    val gptModel: String?,
    val gptPromptSnippet: String?,
    val gptResponse: String?,
    val finalRobotOutput: String,
    val notes: String?
)

