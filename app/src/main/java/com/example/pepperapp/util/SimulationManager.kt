package com.example.pepperapp.util

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.util.Log
import java.util.*

/**
 * Manages Android TTS and Speech Recognition for simulation mode
 * Replaces Pepper's QiSDK voice capabilities
 */
class SimulationManager(private val context: Context) {
    
    companion object {
        private const val TAG = "SimulationManager"
    }
    
    private var tts: TextToSpeech? = null
    private var speechRecognizer: SpeechRecognizer? = null
    private var ttsInitialized = false
    
    // Callbacks
    var onSpeechResult: ((String) -> Unit)? = null
    var onSpeechError: ((String) -> Unit)? = null
    var onTtsComplete: (() -> Unit)? = null
    var onTtsReady: (() -> Unit)? = null  // New callback for TTS ready
    
    fun initializeTts() {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.US)
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    Log.e(TAG, "Language not supported")
                    ttsInitialized = false
                } else {
                    ttsInitialized = true
                    Log.d(TAG, "TTS initialized successfully")
                    onTtsReady?.invoke()  // Notify when ready
                }
            } else {
                Log.e(TAG, "TTS initialization failed")
                ttsInitialized = false
            }
        }
    }
    
    fun speak(text: String, onComplete: (() -> Unit)? = null) {
        if (ttsInitialized && tts != null) {
            // Generate utterance ID once
            val utteranceId = "utteranceId_${System.currentTimeMillis()}"
            
            // Set utterance listener for completion callback
            tts?.setOnUtteranceProgressListener(object : android.speech.tts.UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    Log.d(TAG, "TTS started: $utteranceId")
                }
                
                override fun onDone(utteranceId: String?) {
                    Log.d(TAG, "TTS completed: $utteranceId")
                    onComplete?.invoke()
                    onTtsComplete?.invoke()
                }
                
                override fun onError(utteranceId: String?) {
                    Log.e(TAG, "TTS error: $utteranceId")
                    onComplete?.invoke()
                }
            })
            
            val params = Bundle()
            params.putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, utteranceId)
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, params, utteranceId)
        } else {
            Log.w(TAG, "TTS not initialized, skipping speech")
            onComplete?.invoke()
        }
    }
    
    fun startListening() {
        if (speechRecognizer == null) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
        }
        
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                Log.d(TAG, "Ready for speech")
            }
            
            override fun onBeginningOfSpeech() {
                Log.d(TAG, "Beginning of speech")
            }
            
            override fun onRmsChanged(rmsdB: Float) {}
            
            override fun onBufferReceived(buffer: ByteArray?) {}
            
            override fun onEndOfSpeech() {
                Log.d(TAG, "End of speech")
            }
            
            override fun onError(error: Int) {
                val errorMessage = when (error) {
                    SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
                    SpeechRecognizer.ERROR_CLIENT -> "Client side error"
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Insufficient permissions"
                    SpeechRecognizer.ERROR_NETWORK -> "Network error"
                    SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                    SpeechRecognizer.ERROR_NO_MATCH -> "No match found"
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognizer busy"
                    SpeechRecognizer.ERROR_SERVER -> "Server error"
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Speech timeout"
                    else -> "Unknown error"
                }
                Log.e(TAG, "Speech recognition error: $errorMessage")
                onSpeechError?.invoke(errorMessage)
            }
            
            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    val transcript = matches[0]
                    Log.d(TAG, "Speech result: $transcript")
                    onSpeechResult?.invoke(transcript)
                } else {
                    onSpeechError?.invoke("No speech detected")
                }
            }
            
            override fun onPartialResults(partialResults: Bundle?) {
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    Log.d(TAG, "Partial result: ${matches[0]}")
                }
            }
            
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
        
        speechRecognizer?.startListening(intent)
    }
    
    fun stopListening() {
        speechRecognizer?.stopListening()
    }
    
    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
        speechRecognizer?.destroy()
        tts = null
        speechRecognizer = null
    }
    
    fun isTtsInitialized(): Boolean = ttsInitialized
}

