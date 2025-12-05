package com.example.pepperapp.data

import android.content.Context
import com.example.pepperapp.model.InteractionLogEntry
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.*

object LogManager {
    private val entries = mutableListOf<InteractionLogEntry>()
    private var currentSessionId: String? = null
    private var turnCounter = 0

    fun startSession(sessionId: String) {
        currentSessionId = sessionId
        turnCounter = 0
        entries.clear()
    }

    fun logTurn(entry: InteractionLogEntry) {
        entries.add(entry)
        turnCounter++
    }

    fun endSession() {
        // Session ended, but keep entries for export
        currentSessionId = null
    }

    fun exportToCsv(context: Context): File {
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val fileName = "interaction_logs_$timestamp.csv"
        val file = File(context.getExternalFilesDir(null), fileName)
        
        FileWriter(file).use { writer ->
            // Write header
            writer.append("timestamp,sessionId,turnIndex,userRawSpeech,asrTranscript,")
            writer.append("languageDetected,phqQuestionId,handlingModule,pepperLocalNlpSuccess,")
            writer.append("gptUsed,gptReason,gptModel,gptPromptSnippet,gptResponse,")
            writer.append("finalRobotOutput,notes\n")
            
            // Write entries
            entries.forEach { entry ->
                writer.append("${entry.timestamp},")
                writer.append("${escapeCsv(entry.sessionId)},")
                writer.append("${entry.turnIndex},")
                writer.append("${escapeCsv(entry.userRawSpeech ?: "")},")
                writer.append("${escapeCsv(entry.asrTranscript)},")
                writer.append("${escapeCsv(entry.languageDetected)},")
                writer.append("${escapeCsv(entry.phqQuestionId ?: "")},")
                writer.append("${escapeCsv(entry.handlingModule)},")
                writer.append("${entry.pepperLocalNlpSuccess},")
                writer.append("${entry.gptUsed},")
                writer.append("${escapeCsv(entry.gptReason ?: "")},")
                writer.append("${escapeCsv(entry.gptModel ?: "")},")
                writer.append("${escapeCsv(entry.gptPromptSnippet ?: "")},")
                writer.append("${escapeCsv(entry.gptResponse ?: "")},")
                writer.append("${escapeCsv(entry.finalRobotOutput)},")
                writer.append("${escapeCsv(entry.notes ?: "")}\n")
            }
        }
        
        return file
    }

    private fun escapeCsv(value: String): String {
        return if (value.contains(",") || value.contains("\"") || value.contains("\n")) {
            "\"${value.replace("\"", "\"\"")}\""
        } else {
            value
        }
    }

    fun getCurrentSessionId(): String = currentSessionId ?: UUID.randomUUID().toString()
    
    fun getCurrentTurnIndex(): Int = turnCounter
}

