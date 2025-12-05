package com.example.pepperapp.config

enum class GptMode {
    ENABLED,
    DISABLED
}

object GptConfig {
    // Change this to DISABLED to run experiments without GPT
    var currentGptMode: GptMode = GptMode.ENABLED
    
    fun isGptEnabled(): Boolean = currentGptMode == GptMode.ENABLED
}

