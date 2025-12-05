package com.example.pepperapp.util

object LanguageDetector {
    fun detectLanguage(text: String): String {
        val textLower = text.lowercase()
        
        // Simple heuristic: check for common German words/characters
        val germanIndicators = listOf(
            "nicht", "sch", "der", "die", "das", "und", "ist", "zu", "für",
            "auf", "mit", "über", "ä", "ö", "ü", "ß"
        )
        
        val germanCount = germanIndicators.count { textLower.contains(it) }
        
        // If multiple German indicators found, likely German
        return if (germanCount >= 2) "DE" else "EN"
    }
}

