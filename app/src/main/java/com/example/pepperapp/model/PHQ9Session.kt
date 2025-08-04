package com.example.pepperapp.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "phq9_sessions")
data class PHQ9Session(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val timestamp: Long,
    val responses: List<Int>, // List of scores (0-3) for each question
    val totalScore: Int,
    val severity: String, // "minimal", "mild", "moderate", "moderately_severe", "severe"
    val gptSummary: String
) 