package com.example.pepperapp.model

import java.util.UUID

/**
 * PHQ-9 Session Manager
 * Handles PHQ-9 screening logic, scoring, and state management
 * Synchronized with Python simulation version 2.0
 */
class PHQ9SessionManager {
    companion object {
        const val MAX_RETRIES_PER_QUESTION = 3
        const val TOTAL_QUESTIONS = 9
        const val MAX_SCORE = 27
    }
    
    // Session identification
    var sessionId: String = UUID.randomUUID().toString()
    var startTime: Long = System.currentTimeMillis()
    
    // Scoring state
    var currentQuestionIndex = 0
    val finalScores = MutableList<Int?>(TOTAL_QUESTIONS) { null }
    val attemptsPerQuestion = mutableMapOf<Int, MutableList<Int>>().apply {
        for (i in 0 until TOTAL_QUESTIONS) {
            this[i] = mutableListOf()
        }
    }
    val retryCounts = mutableMapOf<Int, Int>().apply {
        for (i in 0 until TOTAL_QUESTIONS) {
            this[i] = 0
        }
    }
    
    // Status flags
    var isActive = false
    var waitingForConfirmation = false
    var waitingForCrisisAck = false
    var pendingScore: Int? = null
    var pendingConfirmation: String? = null
    
    /**
     * Start a new screening session
     */
    fun startSession() {
        isActive = true
        currentQuestionIndex = 0
        finalScores.fill(null)
        attemptsPerQuestion.forEach { (_, list) -> list.clear() }
        retryCounts.keys.forEach { retryCounts[it] = 0 }
        sessionId = UUID.randomUUID().toString()
        startTime = System.currentTimeMillis()
    }
    
    /**
     * Get current question
     */
    fun getCurrentQuestion(): PHQ9Question? {
        return if (currentQuestionIndex < PHQ9Question.getPHQ9Questions().size) {
            PHQ9Question.getPHQ9Questions()[currentQuestionIndex]
        } else null
    }
    
    /**
     * Check if screening is complete
     */
    fun isComplete(): Boolean = currentQuestionIndex >= TOTAL_QUESTIONS
    
    /**
     * Record a score attempt for current question (not final)
     */
    fun recordAttempt(score: Int) {
        if (score in 0..3) {
            attemptsPerQuestion[currentQuestionIndex]?.add(score)
        }
    }
    
    /**
     * Confirm and finalize the answer for current question
     */
    fun confirmAnswer(score: Int) {
        finalScores[currentQuestionIndex] = score
        waitingForConfirmation = false
        pendingScore = null
        pendingConfirmation = null
    }
    
    /**
     * Increment retry counter for current question
     * Returns true if max retries reached
     */
    fun incrementRetry(): Boolean {
        val current = retryCounts[currentQuestionIndex] ?: 0
        retryCounts[currentQuestionIndex] = current + 1
        return (current + 1) >= MAX_RETRIES_PER_QUESTION
    }
    
    /**
     * Apply fallback score when max retries reached
     * Uses last attempt or 0 if no attempts
     */
    fun applyFallbackScore(): Int {
        val attempts = attemptsPerQuestion[currentQuestionIndex] ?: emptyList()
        val fallback = attempts.lastOrNull() ?: 0
        finalScores[currentQuestionIndex] = fallback
        return fallback
    }
    
    /**
     * Move to next question
     * Returns true if more questions remain, false if complete
     */
    fun moveToNextQuestion(): Boolean {
        currentQuestionIndex++
        return !isComplete()
    }
    
    /**
     * Calculate total PHQ-9 score (0-27)
     */
    fun calculateTotalScore(): Int {
        // Fill any missing scores with 0
        val scores = finalScores.map { it ?: 0 }
        val total = scores.sum()
        
        // Safety clamp
        return when {
            total < 0 -> 0
            total > MAX_SCORE -> MAX_SCORE
            else -> total
        }
    }
    
    /**
     * Get severity classification
     */
    fun getSeverity(): String {
        val total = calculateTotalScore()
        return when {
            total <= 4 -> "minimal"
            total <= 9 -> "mild"
            total <= 14 -> "moderate"
            total <= 19 -> "moderately_severe"
            else -> "severe"
        }
    }
    
    /**
     * Get detailed severity description
     */
    fun getSeverityDescription(): String {
        return when (getSeverity()) {
            "minimal" -> "Minimal depression symptoms. Scores in this range (0-4) typically suggest little to no depressive symptoms."
            "mild" -> "Mild depression symptoms. Scores in this range (5-9) may indicate mild depressive symptoms that might benefit from monitoring."
            "moderate" -> "Moderate depression symptoms. Scores in this range (10-14) suggest moderate depressive symptoms that may warrant professional evaluation."
            "moderately_severe" -> "Moderately severe depression symptoms. Scores in this range (15-19) indicate significant symptoms that would benefit from professional care."
            "severe" -> "Severe depression symptoms. Scores in this range (20-27) suggest severe depressive symptoms requiring immediate professional attention."
            else -> "Unknown severity level."
        }
    }
    
    /**
     * Check if Q9 (suicidality) requires crisis intervention
     */
    fun requiresCrisisProtocol(): Boolean {
        if (currentQuestionIndex == 8) {  // Q9 is index 8
            val score = finalScores[8]
            return score != null && score > 0
        }
        return false
    }
    
    /**
     * Validate final scores and return warnings
     */
    fun validateScores(): List<String> {
        val warnings = mutableListOf<String>()
        
        for (i in 0 until TOTAL_QUESTIONS) {
            when {
                finalScores[i] == null -> 
                    warnings.add("Q${i+1} has no final score, will default to 0")
                finalScores[i] !in 0..3 -> 
                    warnings.add("Q${i+1} score ${finalScores[i]} is invalid (must be 0-3)")
            }
        }
        
        val total = calculateTotalScore()
        if (total > MAX_SCORE) {
            warnings.add("Total score $total exceeds maximum $MAX_SCORE")
        }
        
        return warnings
    }
    
    /**
     * Get complete session summary
     */
    fun getSummary(): Map<String, Any> {
        val total = calculateTotalScore()
        val severity = getSeverity()
        
        return mapOf(
            "session_id" to sessionId,
            "start_time" to startTime,
            "end_time" to System.currentTimeMillis(),
            "final_scores" to finalScores.map { it ?: 0 },
            "total_score" to total,
            "severity" to severity,
            "severity_description" to getSeverityDescription(),
            "retry_counts" to retryCounts.values.toList(),
            "total_retries" to retryCounts.values.sum()
        )
    }
}

